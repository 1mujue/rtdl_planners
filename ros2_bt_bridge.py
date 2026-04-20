import os
import signal
import subprocess
from pathlib import Path
from typing import Tuple, List

def sh_quote(s: str) -> str:
    return "'" + s.replace("'", "'\"'\"'") + "'"

class ROS2BTBridge:
    def __init__(
        self,
        workspace_root: str,
        package_name: str,
        executable_name: str,
        ros_distro: str = "humble",
        use_packages_up_to:bool = False,
        ):
        self.workspace_root = Path(workspace_root).resolve()
        self.package_name = package_name
        self.executable_name = executable_name
        self.ros_distro  =ros_distro
        self.use_packages_up_to = use_packages_up_to

    @property
    def pkg_root(self) -> Path:
        return self.workspace_root / "src" / self.package_name

    @property
    def xml_target_path(self) -> Path:
        return self.pkg_root / "trees" / "plan.xml"

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
    
    def build_package(self, timeout: int = 100) -> Tuple[str, str]:
        cmd = self._build_cmd()
        result = subprocess.run(
            ["bash", "-lc", cmd],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False
        )
        print("Build pkg standard output: \n" + result.stdout)
        print("Build pkg standard error: \n" + result.stderr)
        return result.stdout, result.stderr
        
    
    def _run_cmd(self, extra_args: List[str] | None = None) -> str:
        extra = ""
        if extra_args:
            extra = " " + " ".join(sh_quote(x) for x in extra_args)

        return (
            f"source /opt/ros/{self.ros_distro}/setup.bash && "
            f"cd {sh_quote(str(self.workspace_root))} && "
            f"source install/setup.bash && "
            f"exec ros2 run {sh_quote(self.package_name)} {sh_quote(self.executable_name)}{extra} --mode run"
        )
        
    
    def run_node(self, extra_args: List[str] | None = None) -> Tuple[str, str]:
        cmd = self._run_cmd(extra_args)
        result = subprocess.run(
            ["bash", "-lc", cmd],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout, result.stderr
    
    def _visualize_cmd(self, extra_args: List[str] | None = None) -> str:
        extra = ""
        if extra_args:
            extra = " " + " ".join(sh_quote(x) for x in extra_args)

        return (
            f"source /opt/ros/{self.ros_distro}/setup.bash && "
            f"cd {sh_quote(str(self.workspace_root))} && "
            f"source install/setup.bash && "
            f"exec ros2 run {sh_quote(self.package_name)} {sh_quote(self.executable_name)}{extra} --mode visualize"
        )

    def visualize_bt(self, extra_args: List[str] | None = None) -> Tuple[str, str]:
        cmd = self._visualize_cmd(extra_args)
        result = subprocess.run(
            ["bash", "-lc", cmd],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout, result.stderr