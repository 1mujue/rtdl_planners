import json
import rclpy

from world_state_client import WorldStateClient
from prompt_builder import build_prompts
from reply_parser import parse_planner_reply
from typing import List, Dict

class TaskPlanner:
    def __init__(self, skills_path: str, llm_client):
        self.skills_path = skills_path
        self.llm_client = llm_client

        if not rclpy.ok():
            rclpy.init()

        self.ws_client = WorldStateClient()

        self.last_world_state = None
        self.last_system_prompt = None
        self.last_user_promt = None

        self.last_result = None

        self.last_rtdl = None
        self.last_bt = None
    
    def close(self):
        self.ws_client.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    
    def load_skills(self) -> List[Dict]:
        with open(self.skills_path, "r", encoding="utf-8") as f:
            return json.load(f)
        
    def plan(self, user_task: str) -> Dict:
        world_state = self.ws_client.fetch()
        skills = self.load_skills()

        system_prompt, user_prompt = build_prompts(
            user_task=user_task,
            world_state=world_state,
            skills=skills,
        )

        raw_reply = self.llm_client.generate(system_prompt, user_prompt)
        result = parse_planner_reply(raw_reply)

        self.last_world_state = world_state

        self.last_system_prompt = system_prompt
        self.last_user_promt = user_prompt

        self.last_result = result
        self.last_rtdl = self.last_result["rtdl"]
        
        return result
    
    def get_last_prompt(self) -> str:
        return "system prompt: " + self.last_system_prompt + "\nuser_prompt: " + self.last_user_promt