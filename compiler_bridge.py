import subprocess
import tempfile
from pathlib import Path

class RTDLCompilerBridge:
    def __init__(self, compiler_path: str):
        self.compiler_path = compiler_path

    def compile(self, rtdl_text: str) -> str:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            rtdl_file = tmpdir / "plan.rtdl"
            bt_file = tmpdir / "plan.xml"

            rtdl_file.write_text(rtdl_text, encoding="utf-8")

            result = subprocess.run(
                [self.compiler_path, "--rtdl-in", str(rtdl_file), "--bt-out", str(bt_file)],
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode != 0:
                raise RuntimeError(
                    f"Compiler failed\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
                )
            
            return bt_file.read_text(encoding="utf-8")

