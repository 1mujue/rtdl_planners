import json
import time
import traceback
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Optional

from conductor import Conductor
from webots_bridge import ResetWorldClient


@dataclass
class BenchmarkRecord:
    round: int
    model: str
    level: int
    task: str

    status: str

    llm_time_sec: Optional[float] = None

    rtdl_valid: Optional[bool] = None
    rtdl_error: Optional[str] = None

    execution_time_sec: Optional[float] = None
    execution_success: Optional[bool] = None
    execution_message: Optional[str] = None

    plan_summary: Optional[str] = None
    assumptions: Optional[list[str]] = None
    rtdl: Optional[str] = None

    error_type: Optional[str] = None
    error_message: Optional[str] = None
    traceback: Optional[str] = None

    # manual handle.
    manual_logic_completeness: Optional[int] = None
    manual_logic_correct: Optional[int] = None
    manual_collision_observed: Optional[int] = None
    manual_notes: str = ""


def now_timestamp() -> str:
    return time.strftime("%Y%m%d_%H%M%S")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def append_jsonl(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def validate_rtdl(conductor: Conductor, rtdl: str) -> tuple[bool, str, Optional[str]]:
    """
    return:
        (True, bt_xml, None): success
        (False, None, error_message): fail
    """
    try:
        bt_xml, stdout, stderr = conductor.compile_rtdl(rtdl)
        if stderr is None or not stderr:
            return True, bt_xml, None
        else:
            return False, None, stderr
    except Exception:
        return False, None, stderr



class BenchmarkRunner:
    def __init__(
        self,
        *,
        model: str,
        level: int,
        task: str,
        repeat: int,
        output_dir: str = "benchmark_results"
    ):
        self.model = model
        self.level = level
        self.task = task
        self.repeat = repeat

        self.run_dir = Path(output_dir) / f"{now_timestamp()}_{model}_level{level}"
        self.summary_jsonl = self.run_dir / "summary.jsonl"

        self.conductor = Conductor(model_alias=model)
        self.reset_client = ResetWorldClient()

    def run(self) -> None:
        metadata = {
            "model": self.model,
            "level": self.level,
            "task": self.task,
            "repeat": self.repeat,
            "created_at": now_timestamp(),
        }
        write_json(self.run_dir / "metadata.json", metadata)

        for i in range(self.repeat):
            print(f"\n[Benchmark] round {i + 1}/{self.repeat}")
            record = self.run_one_round(i)

            record_dict = asdict(record)

            round_dir = self.run_dir / f"round_{i:03d}"
            write_json(round_dir / "record.json", record_dict)

            if record.rtdl:
                write_text(round_dir / "generated.rtdl", record.rtdl)

            append_jsonl(self.summary_jsonl, record_dict)

        print(f"\n[Benchmark] finished.")
        print(f"[Benchmark] results saved to: {self.run_dir}")

    def wait_backend_ready_after_reset(self) -> None:
        time.sleep(0.2)

    def run_one_round(self, round_id: int) -> BenchmarkRecord:
        record = BenchmarkRecord(
            round=round_id,
            model=self.model,
            level=self.level,
            task=self.task,
            status="started",
        )

        try:
            # 1. reset world
            print("[Benchmark] reset world...")
            self.reset_client.reset()
            self.wait_backend_ready_after_reset()

            # 2. LLM planning
            print("[Benchmark] planning RTDL...")
            t0 = time.perf_counter()
            plan_result = self.conductor.plan_rtdl(self.task)
            t1 = time.perf_counter()

            record.llm_time_sec = t1 - t0

            record.plan_summary = plan_result.get("plan_summary")
            record.assumptions = plan_result.get("assumptions", [])
            record.rtdl = plan_result.get("rtdl")

            if not record.rtdl:
                record.status = "plan_failed"
                record.error_type = "EmptyRTDL"
                record.error_message = "LLM returned empty RTDL."
                return record

            # 3. validate RTDL
            print("[Benchmark] validate RTDL...")
            valid, bt_xml, error = validate_rtdl(self.conductor, record.rtdl)

            record.rtdl_valid = valid
            record.rtdl_error = error

            if not valid:
                print("[Benchmark] RTDL invalid. Skip execution.")
                record.status = "rtdl_invalid"
                return record
            
            bout, berr = self.conductor.build_ros2_bt_pkg(bt_xml)
            # 4. execute RTDL
            print("[Benchmark] execute RTDL...")
            t2 = time.perf_counter()
            exec_o, exec_e = self.conductor.run()
            t3 = time.perf_counter()

            record.execution_time_sec = t3 - t2
            record.execution_success = True
            if exec_o is not None:
                record.execution_message = exec_o
            if exec_e is not None:
                record.execution_message += "\n" + exec_e
            record.status = "executed"

            return record

        except Exception as e:
            record.status = "error"
            record.error_type = type(e).__name__
            record.error_message = str(e)
            record.traceback = traceback.format_exc()
            return record
        


def default_task_for_level(level: int) -> str:
    if level == 1:
        return "Pick up the CUP and place it on the TABLE."

    if level == 2:
        return "请让机器人取出架子里面的药瓶，并把它放到医疗台上。"

    if level == 3:
        return "请让机器人从三层箱堆中取出第二层的蓝色箱子，将它放到检查台上，并把最上方的绿色箱子放回最下方的箱子上。"

    raise ValueError(f"Unknown level: {level}")


def test_entry(args, backend=None) -> None:
    task = default_task_for_level(args.level)
    repeat = getattr(args, "repeat", 1)

    runner = BenchmarkRunner(
        model=args.model,
        level=args.level,
        task=task,
        repeat=repeat,
        output_dir=getattr(args, "output_dir", "benchmark_results"),
    )

    runner.run()