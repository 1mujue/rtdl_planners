import argparse
import os
import signal
import subprocess
from window import GUI_entry
from benchmark import test_entry
from dataclasses import dataclass

@dataclass
class BackendHandle:
    server_proc: subprocess.Popen
    webots_proc: subprocess.Popen

    def shutdown(self):
        for proc in [self.webots_proc, self.server_proc]:
            if proc is None:
                continue
            if proc.poll() is not None:
                continue

            try:
                os.killpg(proc.pid, signal.SIGTERM)
                proc.wait(timeout=5)
            except Exception:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except Exception:
                    pass

def _check_env(var, name:str) -> None:
    if var is None:
        raise ValueError(f"The env var '{name}' is not set.")

LEVEL_CONFIG = {
    1: {
        "world": "level1.wbt",
        "entity_config": "level1_en.yaml",
    },
    2: {
        "world": "level2.wbt",
        "entity_config": "level2_en.yaml",
    },
    3: {
        "world": "level3.wbt",
        "entity_config": "level3_en.yaml",
    },
}

def launch_backend(level: int) -> BackendHandle:
    ros2_exec_pkg = os.environ.get("ROS2_EXECUTION_PKG")
    _check_env(ros2_exec_pkg, "ROS2_EXECUTION_PKG")

    ros2_exec_tar = os.environ.get("ROS2_EXECUTION_TAR")
    _check_env(ros2_exec_tar, "ROS2_EXECUTION_TAR")

    ros2_webots_pkg = os.environ.get("ROS2_WEBOTS_PKG")
    _check_env(ros2_webots_pkg, "ROS2_WEBOTS_PKG")

    ros2_webots_tar = os.environ.get("ROS2_WEBOTS_TAR")
    _check_env(ros2_webots_tar, "ROS2_WEBOTS_TAR")

    if level not in LEVEL_CONFIG:
        raise ValueError(f"Unknown level: {level}")

    world = LEVEL_CONFIG[level]["world"]
    entity_config = LEVEL_CONFIG[level]["entity_config"]

    launch_server_cmd = f"ros2 run {ros2_exec_pkg} {ros2_exec_tar}"

    launch_webots_cmd = (
        f"ros2 launch {ros2_webots_pkg} {ros2_webots_tar} "
        f"world:={world} "
        f"entity_config:={entity_config}"
    )

    server_proc = subprocess.Popen(
        ["bash", "-lc", launch_server_cmd],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    )

    webots_proc = subprocess.Popen(
        ["bash", "-lc", launch_webots_cmd],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    )

    return BackendHandle(
        server_proc=server_proc,
        webots_proc=webots_proc,
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, required=True)
    parser.add_argument("--level", type=int, required=True)
    parser.add_argument("--type", type=str, required=True, choices=["GUI", "test"])
    parser.add_argument("--repeat", type=int, default=5, help="Repeat count for benchmark")
    parser.add_argument("--output-dir", type=str, default="benchmark_results")
    args = parser.parse_args()

    backend = launch_backend(args.level)

    try:
        if args.type == "GUI":
            GUI_entry(args=args, backend=backend)
        elif args.type == "test":
            test_entry(args=args, backend=backend)
    finally:
        backend.shutdown()
    