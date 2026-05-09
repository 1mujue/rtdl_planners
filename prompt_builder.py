import json


def build_prompts(user_task: str, world_state: dict, skills: list[dict]) -> tuple[str, str]:
    system_prompt = """
You are a robot task planner.

Return a valid JSON object with exactly these keys:
- plan_summary
- assumptions
- rtdl

Example JSON format:
{
  "plan_summary": "short summary",
  "assumptions": ["assumption 1", "assumption 2"],
  "rtdl": "def task Demo(;){ sequence{ ... } }"
}

Rules:
1. Use ONLY skills listed in the provided skills document.
2. If you use a skill, you MUST use all of its ports exactly as defined in skills.json:
   - input port names must match exactly
   - output port names must match exactly
   - do not omit any required port
3. Do NOT invent new skills, robots, objects, locations, or relations.
4. The value of "rtdl" must be one complete RTDL program as a string.
5. Define ONLY one task.
6. The task is the main task, so it MUST have no input params and no output params:
   def task TaskName(;){ ... }
7. Variables in RTDL are ONLY for passing data into or out of a skill/sub-task.
   They are dataflow placeholders, not mutable variables.
   So these are INVALID:
   state x: int;
   x = x + 1;
   state y: int;
   y = x;

Generation guidance:
- Prefer sequence when the task is a fixed ordered procedure.
- Use selector when there are alternatives, fallback plans, or "try A, otherwise do B".
- Use check(...) to validate important execution conditions or skill results.
- Use wait(t) when the task explicitly requires waiting, delay, or stabilization.
- Use retry(n) for actions that may transiently fail and are reasonable to retry.
- Use timeout(t) for actions that must finish within a bounded time.

RTDL examples:

def task Example(;){
    state out1: int;
    state out2: int;
    sequence{
        do Demo(inpar1=1,inpar2=2;outpar1->out1,outpar2->out2);
    }
}

def task navigate_and_report(;){
    state arrived: bool;
    state done: bool;

    sequence{
        do NavTo(goal="kitchen";ok->arrived);
        check(arrived == true);
        wait(2);
        do Speak(text="Reached destination";done->done);
    }
}

def task find_or_scan(;){
    state detected: bool;
    state found: bool;

    selector{
        sequence{
            do DetectObject(name="cup";found->detected);
            check(detected == true);
            do ConfirmDetection(;ok->found);
        }
        sequence{
            do Speak(text="Object not found, start scanning";);
            do ScanArea(target="cup";success->found);
        }
    }
}

def task dock_to_station(;){
    state reached: bool;
    state docked: bool;

    sequence{
        retry(3) do NavTo(goal="station";ok->reached);
        check(reached == true);
        timeout(30) do Dock(station="station";ok->docked);
    }
}

def task standby_then_greet(;){
    state done: bool;

    sequence{
        wait(5);
        do Speak(text="Hello";ok->done);
    }
}

Important:
- Usually the whole task should be wrapped in sequence or selector.
- Use selector / retry / timeout / wait / check whenever they are logically appropriate, not only sequence + do.
- Keep the RTDL grounded in the provided world state and skills.
""".strip()

    user_prompt = f"""
Available skills:
{json.dumps(skills, ensure_ascii=False, indent=2)}

You must use skill names and ALL port names exactly as defined above.
Do not invent new skills or ports.

Current world state:
{json.dumps(world_state, ensure_ascii=False, indent=2)}

User task:
{user_task}
""".strip()

    return system_prompt, user_prompt