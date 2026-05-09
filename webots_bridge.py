import json
import threading
from typing import Any

import rclpy
from rclpy.node import Node
from rosidl_runtime_py.convert import message_to_ordereddict

from rtdl_demo_interfaces.srv import GetWorldState
from std_srvs.srv import Trigger


class WorldStateClient(Node):
    _instance = None
    _instance_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, service_name: str = "/get_world_state"):
        # 关键：防止 __init__ 被重复执行
        if getattr(self, "_initialized", False):
            if service_name != self.service_name:
                raise ValueError(
                    f"WorldStateClient has already been initialized with "
                    f"service_name={self.service_name}, but got {service_name}"
                )
            return

        super().__init__("planner_world_state_client")

        self.service_name = service_name
        self.cli = self.create_client(GetWorldState, service_name)
        self._call_lock = threading.Lock()

        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info(
                f"service {service_name} not available. wait again..."
            )

        self._initialized = True

    def fetch_dict(self) -> dict[str, Any]:
        req = GetWorldState.Request()

        with self._call_lock:
            future = self.cli.call_async(req)
            rclpy.spin_until_future_complete(self, future=future)

        result = future.result()
        if result is None:
            raise RuntimeError(f"Failed to call {self.service_name} service")

        state_dict = message_to_ordereddict(result.state)
        return dict(state_dict)

    def fetch_json(self) -> str:
        state_dict = self.fetch_dict()
        return json.dumps(state_dict, ensure_ascii=False, indent=4)
    
class ResetWorldClient(Node):
    def __init__(self, service_name: str = "/reset_world"):
        super().__init__("reset_world_client")
        self.service_name = service_name
        self.cli = self.create_client(Trigger, service_name)

        if not self.cli.wait_for_service(timeout_sec=10.0):
            raise RuntimeError(f"Service {service_name} is not available.")

    def reset(self) -> None:
        req = Trigger.Request()
        future = self.cli.call_async(req)
        rclpy.spin_until_future_complete(self, future)

        result = future.result()
        if result is None:
            raise RuntimeError(f"Failed to call {self.service_name}")

        if not result.success:
            raise RuntimeError(f"Reset failed: {result.message}")