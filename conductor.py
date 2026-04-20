from planner import TaskPlanner
from llm_client import DeepSeekClient
from compiler_bridge import RTDLCompilerBridge
from ros2_bt_bridge import ROS2BTBridge
from world_state_client import WorldStateClient
from typing import Dict, Tuple

class Conductor:
    def __init__(self):
        self.planner = TaskPlanner(
            skills_path="skills.json",
            llm_client=DeepSeekClient(
                model="deepseek-chat",
                base_url="https://api.deepseek.com",
                max_tokens=2048,
            )
        )
        self.WSClient = WorldStateClient()
        self.rtdlCompiler = RTDLCompilerBridge("/home/mujue/pros/ud/rtdlc/build/RTDLC")
        self.ros2btRunner = ROS2BTBridge(
            workspace_root="/home/mujue/pros/ud/ros2_rtdl",
            package_name="rtdl_demo_bt_test",
            executable_name="bt_runner",
            ros_distro="humble",
        )
        
        self.last_bt = None
        self.last_rtdl = None
    def get_world_state(self) -> Dict:
        return self.WSClient.fetch()
    
    def plan_rtdl(self, task:str) -> Dict:
        result = self.planner.plan(task)
        self.last_rtdl = result["rtdl"]
        return result
    
    def compile_rtdl(self) -> Tuple[str, str, str]:
        bt_xml, stdout, stderr = self.rtdlCompiler.compile(rtdl_text=self.last_rtdl)
        self.last_bt = bt_xml
        return bt_xml, stdout, stderr

    def build_ros2_bt_pkg(self) -> Tuple[str, str]:
        self.ros2btRunner.write_xml(self.last_bt)
        return self.ros2btRunner.build_package()

    def run(self) -> Tuple[str, str]:
        return self.ros2btRunner.run_node()

    def visualize_bt(self) -> Tuple[str, str]:
        return self.ros2btRunner.visualize_bt()