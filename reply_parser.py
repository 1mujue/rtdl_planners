import json
import re
from typing import Dict, List

def extract_json_block(text: str) -> Dict:
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in LLM reply.")

    json_str = match.group(0)
    return json.loads(json_str)

def parse_planner_reply(text: str) -> Dict:
    data = extract_json_block(text)

    requried_keys = ["plan_summary","assumptions","rtdl"]
    for key in requried_keys:
        if key not in data:
            raise ValueError(f"Missing key in LLM reply: {key}")
        
    if not isinstance(data["plan_summary"], str):
        raise ValueError("plan_summary must be a string")
    if not isinstance(data["assumptions"], list):
        raise ValueError("assumptions must be a list")
    if not isinstance(data["rtdl"], str):
        raise ValueError("rtdl must be a string")

    return data