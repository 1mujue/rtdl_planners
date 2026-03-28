from planner import TaskPlanner
from llm_client import DeepSeekClient
from compiler_bridge import RTDLCompilerBridge
    
def help():
    print("RTDL Planner Terminal")
    print("Commands:")
    print("  /plan <task>")
    print("  /compile")
    print("  /state")
    print("  /prompt")
    print("  /last")
    print("  /quit")
    
def main():
    planner = TaskPlanner(
        skills_path="skills.json",
        llm_client=DeepSeekClient(
            model="deepseek-chat",
            base_url="https://api.deepseek.com",
            max_tokens=2048,
        )
    )
    rtdlCompiler = RTDLCompilerBridge("../rtdlc/build/RTDLC")

    help()

    while True:
        try:
            line = input("> ").strip()
        except EOFError:
            break

        if not line:
            continue

        if line == "/quit":
            break

        if line == "/state":
            if planner.last_world_state is None:
                print("No world state loaded yet.")
            else:
                print(planner.last_world_state)
            continue

        if line == "/prompt":
            if planner.last_prompt is None:
                print("No prompt generated yet.")
            else:
                print(planner.last_prompt)
            continue

        if line == "/last":
            if planner.last_result is None:
                print("No result yet.")
            else:
                print("Plan summary:")
                print(planner.last_result["plan_summary"])
                print("\nAssumptions:")
                for item in planner.last_result["assumptions"]:
                    print("-", item)
                print("\nRTDL:")
                print(planner.last_result["rtdl"])
            continue

        if line.startswith("/plan "):
            task = line[len("/plan "):].strip()
            if not task:
                print("Task is empty.")
                continue

            try:
                result = planner.plan(task)
                print("Plan summary:")
                print(result["plan_summary"])
                print("\nAssumptions:")
                for item in result["assumptions"]:
                    print("-", item)
                print("\nRTDL:")
                print(result["rtdl"])
            except Exception as e:
                print(f"[ERROR] {e}")

            continue

        if line == "/compile":
            rtdl_text = planner.last_result["rtdl"]
            bt_xml = rtdlCompiler.compile(rtdl_text=rtdl_text)
            print("Compile output(BT XML):")
            print(bt_xml)
            planner.last_bt = bt_xml

        print("Unknown command.")

if __name__ == "__main__":
    main()