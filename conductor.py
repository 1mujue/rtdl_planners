from planner import TaskPlanner
from llm_client import build_llm_client
from compiler_bridge import RTDLCompilerBridge
from ros2_bt_bridge import ROS2BTBridge
from webots_bridge import WorldStateClient
from typing import Dict, Tuple
import os

class Conductor:
    def __init__(self, model_alias: str):
        self.planner = TaskPlanner(
            skills_path="skills.json",
            llm_client=build_llm_client(model_alias=model_alias)
        )
        self.WSClient = WorldStateClient()

        rtdlc_exec_path = os.environ.get("RTDLC_EXEC_PATH")
        ws_path = os.environ.get("ROS2_WORKSPACE_PATH")
        bt_runner_pkg = os.environ.get("ROS2_BT_RUNNER_PKG")
        bt_runner_tar = os.environ.get("ROS2_BT_RUNNER_TAR")
        self.rtdlCompiler = RTDLCompilerBridge(f"{rtdlc_exec_path}/RTDLC")
        self.ros2btRunner = ROS2BTBridge(
            workspace_root=ws_path,
            package_name=bt_runner_pkg,
            executable_name=bt_runner_tar,
            ros_distro=os.environ.get("ROS_DISTRO"),
        )
    def get_world_state(self) -> Dict:
        return self.WSClient.fetch()
    
    def plan_rtdl(self, task:str) -> Dict:
        result = self.planner.plan(task)
        self.last_rtdl = result["rtdl"]
        return result
    
    def compile_rtdl(self, rtdl: str) -> Tuple[str, str, str]:
        bt_xml, stdout, stderr = self.rtdlCompiler.compile(rtdl_text=rtdl)
        self.last_bt = bt_xml
        return bt_xml, stdout, stderr

    def build_ros2_bt_pkg(self, bt_xml: str) -> Tuple[str, str]:
        self.ros2btRunner.write_xml(bt_xml)
        return self.ros2btRunner.build_package()

    def run(self) -> Tuple[str, str]:
        return self.ros2btRunner.run_node()

    def visualize_bt(self) -> Tuple[str, str]:
        return self.ros2btRunner.visualize_bt()