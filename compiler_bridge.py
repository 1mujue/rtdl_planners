import subprocess
import tempfile
from pathlib import Path
from typing import Tuple

class RTDLCompilerBridge:
    def __init__(self, compiler_path: str):
        self.compiler_path = compiler_path

    def compile(self, rtdl_text: str) -> Tuple[str, str, str]:
        compiler_path = Path(self.compiler_path).resolve()
        compiler_dir = compiler_path.parent

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            rtdl_file = tmpdir / "plan.rtdl"
            bt_file = tmpdir / "plan.xml"

            rtdl_file.write_text(rtdl_text, encoding="utf-8")

            cmd = [
                str(compiler_path),
                "--rtdl-in", str(rtdl_file),
                "--bt-out", str(bt_file),
                "--ros2-ws", "/home/mujue/pros/ud/ros2_rtdl"
            ]

            result = subprocess.run(
                cmd,
                cwd=str(compiler_dir),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                timeout=20,
            )

            if result.returncode != 0:
                raise RuntimeError(
                    f"Compiler failed with return code {result.returncode}\n"
                    f"stdout:\n{result.stdout}\n"
                    f"stderr:\n{result.stderr}"
                )

            if not bt_file.exists():
                raise RuntimeError(
                    "Compiler finished but did not generate plan.xml\n"
                    f"stdout:\n{result.stdout}\n"
                    f"stderr:\n{result.stderr}"
                )

            return bt_file.read_text(encoding="utf-8"), result.stdout, result.stderr
