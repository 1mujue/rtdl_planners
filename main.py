from planner import TaskPlanner
from llm_client import DeepSeekClient
from compiler_bridge import RTDLCompilerBridge
from ros2_bt_bridge import ROS2BTBridge
    
def help():
    print("RTDL Planner Terminal")
    print("Commands:")
    print("  /plan <task> # Input a natural language description of the task, and we will output rtdl.")
    print("  /compile # compile the LAST generated rtdl into xml (the tree structure description file of bt).")
    print("  /state # get the LAST state of the robot world.")
    print("  /prompt # get the last prompt sent to agent.")
    print("  /last # get the last reply of agent.")
    print("  /quit # quit the process.")
    print("  /set_rtdl <RTDL> # replace the LAST generated rtdl with your input.")
    print("  /run # run the LAST generated bt xml.")
    
def main():
    planner = TaskPlanner(
        skills_path="skills.json",
        llm_client=DeepSeekClient(
            model="deepseek-chat",
            base_url="https://api.deepseek.com",
            max_tokens=2048,
        )
    )
    rtdlCompiler = RTDLCompilerBridge("/home/mujue/pros/ud/rtdlc/build/RTDLC")
    ros2btRunner = ROS2BTBridge(
        workspace_root="/home/mujue/pros/ud/ros2_rtdl",
        package_name="rtdl_demo_bt",
        executable_name="bt_runner",
        ros_distro="humble",
        xml_name="plan.xml"
    )


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

        elif line == "/state":
            if planner.last_world_state is None:
                print("No world state loaded yet.")
            else:
                print(planner.last_world_state)

        elif line == "/prompt":
            print(planner.get_last_prompt())

        elif line == "/last":
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

        elif line.startswith("/plan "):
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

        elif line.startswith("/set_rtdl"):
            user_rtdl = line[len("/set_rtdl "):].strip()
            if not user_rtdl:
                print("The rtdl is empty.")
                continue
            planner.last_rtdl = user_rtdl
            print("Set RTDL successfully.")

        elif line == "/compile":
            bt_xml = rtdlCompiler.compile(rtdl_text=planner.last_rtdl)
            print("Compile output(BT XML):")
            print(bt_xml)
            planner.last_bt = bt_xml

        elif line == "/build":
            ros2btRunner.write_xml(planner.last_bt)
            ros2btRunner.build_package()
            print("Build succeeded.")
            
        elif line == "/run":
            ros2btRunner.run_node()

        else:
            print("Unknown command.")

if __name__ == "__main__":
    main()