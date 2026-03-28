import json
import rclpy
from rclpy.node import Node
from typing import Dict
from rtdl_demo_interfaces.srv import GetWorldState
from rosidl_runtime_py.convert import message_to_ordereddict

class WorldStateClient(Node):
    def __init__(self, service_name: str = "/get_world_state"):
        super().__init__("planner_world_state_client")
        self.cli = self.create_client(GetWorldState, service_name)

        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info(f"service {service_name} not available. wait again...")

    def fetch(self) -> Dict:
        req = GetWorldState.Request()

        future = self.cli.call_async(req)
        rclpy.spin_until_future_complete(self, future=future)

        if future.result() is None:
            raise RuntimeError("Failed to call /get_world_state service")
        
        res = future.result()
        state_dict = message_to_ordereddict(res.state)
        return json.dumps(state_dict, ensure_ascii=False, indent=4)
