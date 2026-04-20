import json


def build_prompts(user_task: str, world_state: dict, skills: list[dict]) -> tuple[str, str]:
    system_prompt = """
You are a robot task planner.

You must generate a valid json object.
The json object must contain exactly these keys:
- plan_summary
- assumptions
- rtdl

Example json format:
{
  "plan_summary": "short summary",
  "assumptions": ["assumption 1", "assumption 2"],
  "rtdl": "task Demo { ... }"
}

Rules:
- Only use skills listed in the provided skills document. You MUST make sure every port's name is completely same as described in skills.json and every port MUST be used.
- Do not invent robots, objects, or relations that are not present in the world state.
- The value of "rtdl" must be a complete RTDL program as a string.

An example of rtdl(assuming we have a skill Demo(inpar1, inpar2, outpar1, outpar2))
def task Example(t1: int, t2:int; t3: int, t4: int){
    Sequence{
        do Demo(inpar1=t1,inpar2=t2;outpar1->t3,outpar2->t4);
    }
}

If you have already know the exact value of t1, t2(for example, 1 and 2), then you don't need to 
write them as params of 'task Example'; instead, you can write like:
def task Example(;t3: int, t4: int){
    Sequence{
        do Demo(inpar1=1,inpar2=2;outpar1->t3,outpar->t4);
    }
}
Moreover, if a task doesn't need to pass out any params, which in 'task Example' means t3 and t4
are redundant, then you can write it like:
def task Example(;){
    state local_out1: int;
    state local_out2: int;
    Sequence{
        do Demo(inpar1=1,inpar2=2;outpar1->local_out1,outpar2->local_out2);
    }
}

More examples:

def task navigate_and_report(target: string; success: bool) {
    state arrived: bool;

    sequence {
        do NavTo(goal = target; ok -> arrived);
        check(arrived == true);
        wait(2);
        do Speak(text = "Reached destination"; done -> success);
    }
}

def task find_or_scan(item: string; found: bool) {
    state detected: bool;

    selector {
        sequence {
            do DetectObject(name = item; found -> detected);
            check(detected == true);
            do ConfirmDetection(; ok -> found);
        }

        sequence {
            do Speak(text = "Object not found, start scanning"; );
            do ScanArea(target = item; success -> found);
        }
    }
}

def task dock_to_station(station: string; docked: bool) {
    state reached: bool;

    sequence {
        retry(3) do NavTo(goal = station; ok -> reached);
        check(reached == true);
        timeout(30) do Dock(station = station; ok -> docked);
    }
}

def task standby_then_greet(; done: bool) {
    sequence {
        wait(5);
        do Speak(text = "Hello"; ok -> done);
    }
}

KEY: the variables in rtdl are ONLY used to pass in and out params of a skill or a sub-task,
in other word, they are the representation of data flowing as the task being executed. That means,
The assign operation can ONLY happen when do a skill or call a sub-task, and these statement is invalid:
state x: int;
x = x + 1;
state y: int;
y = x; 

Usually, if a task is the main task, then it doesn't need any in and out params.

""".strip()

    user_prompt = f"""
Available skills:
{json.dumps(skills, ensure_ascii=False, indent=2)}

Note that you have to make sure that you use ALL ports of a skill if you use it,
and you CAN'T invent new skills.

Current world state:
{json.dumps(world_state, ensure_ascii=False, indent=2)}

User task:
{user_task}
""".strip()

    return system_prompt, user_prompt