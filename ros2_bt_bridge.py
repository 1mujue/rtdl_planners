import os
import signal
import subprocess
from pathlib import Path

def sh_quote(s: str) -> str:
    return "'" + s.replace("'", "'\"'\"'") + "'"

class ROS2BTBridge:
    def __init__(
        self,
        workspace_root: str,
        package_name: str,
        executable_name: str,
        ros_distro: str = "humble",
        xml_name: str = "plan.xml",
        use_packages_up_to:bool = False,
        ):
        self.workspace_root = Path(workspace_root).resolve()
        self.package_name = package_name
        self.executable_name = executable_name
        self.ros_distro  =ros_distro
        self.xml_name = xml_name
        self.use_packages_up_to = use_packages_up_to
        self.proc: subprocess.Popen | None = None

    @property
    def pkg_root(self) -> Path:
        return self.workspace_root / "src" / self.package_name

    @property
    def xml_target_path(self) -> Path:
        return self.pkg_root / "trees" / self.xml_name

    def write_xml(self, bt_xml: str) -> Path:
        target = self.xml_target_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(bt_xml, encoding="utf-8")
        return target

    def _build_cmd(self) -> str:
        select_flag = "--packages-up-to" if self.use_packages_up_to else "--packages-select"
        return (
            f"source /opt/ros/{self.ros_distro}/setup.bash &&"
            f"cd {sh_quote(str(self.workspace_root))} &&"
            f"colcon build {select_flag} {sh_quote(self.package_name)}"
        )
    
    def build_package(self, timeout: int = 100) -> None:
        cmd = self._build_cmd()
        result = subprocess.run(
            ["bash", "-lc", cmd],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
            check=False
        )
        print(result.stdout)
        if result.returncode != 0:
            raise RuntimeError(
                f"colcon build failed with code {result.returncode}\n"
                f"{result.stdout}"
            )
    
    def _run_cmd(self, extra_args: list[str] | None = None) -> str:
        extra = ""
        if extra_args:
            extra = " " + " ".join(sh_quote(x) for x in extra_args)

        return (
            f"source /opt/ros/{self.ros_distro}/setup.bash && "
            f"cd {sh_quote(str(self.workspace_root))} && "
            f"source install/setup.bash && "
            f"exec ros2 run {sh_quote(self.package_name)} {sh_quote(self.executable_name)}{extra} --xml-name {self.xml_name}"
        )
        
    
    def run_node(self, extra_args: list[str] | None = None) -> subprocess.Popen:
        if self.proc is not None and self.proc.poll() is None:
            raise RuntimeError("ROS2 node is already running")

        cmd = self._run_cmd(extra_args)
        self.proc = subprocess.Popen(
            ["bash", "-lc", cmd],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            preexec_fn=os.setsid,  # 便于整组进程停止
        )
        return self.proc

    def stop_node(self, force: bool = False) -> None:
        if self.proc is None or self.proc.poll() is not None:
            return

        pgid = os.getpgid(self.proc.pid)
        os.killpg(pgid, signal.SIGKILL if force else signal.SIGTERM)

        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(pgid, signal.SIGKILL)
            self.proc.wait(timeout=5)

    def deploy_and_run(self, bt_xml: str, extra_args: list[str] | None = None) -> subprocess.Popen:
        xml_path = self.write_xml(bt_xml)
        print(f"BT XML written to: {xml_path}")
        self.build_package()
        return self.run_node(extra_args)