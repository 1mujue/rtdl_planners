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

        self.skills= None
        self.ws_client = WorldStateClient()
        self.last_system_prompt = None
        self.last_user_prompt = None
    
    def close(self):
        self.ws_client.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    
    def load_skills(self) -> None:
        with open(self.skills_path, "r", encoding="utf-8") as f:
            self.skills = json.load(f)
        
    def plan(self, user_task: str) -> Dict:
        world_state = self.ws_client.fetch()
        print("The world state for plan: \n" + world_state)
        system_prompt, user_prompt = build_prompts(
            user_task=user_task,
            world_state=world_state,
            skills=self.skills,
        )

        raw_reply = self.llm_client.generate(system_prompt, user_prompt)
        result = parse_planner_reply(raw_reply)

        self.last_world_state = world_state

        self.last_system_prompt = system_prompt
        self.last_user_prompt = user_prompt
        
        return result
    
    def get_last_prompt(self) -> str:
        return "system prompt: " + self.last_system_prompt + "\nuser_prompt: " + self.last_user_prompt