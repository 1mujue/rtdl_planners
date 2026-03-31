import subprocess
import tempfile
from pathlib import Path

class RTDLCompilerBridge:
    def __init__(self, compiler_path: str):
        self.compiler_path = compiler_path

    def compile(self, rtdl_text: str) -> str:
        compiler_path = Path(self.compiler_path).resolve()
        compiler_dir = compiler_path.parent

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            rtdl_file = tmpdir / "plan.rtdl"
            bt_file = tmpdir / "plan.xml"

            print("The rtdl going to be compiled:")
            print(rtdl_text)
            rtdl_file.write_text(rtdl_text, encoding="utf-8")

            cmd = [
                str(compiler_path),
                "--rtdl-in", str(rtdl_file),
                "--bt-out", str(bt_file),
            ]

            print("Running:", cmd)
            print("cwd:", compiler_dir)

            result = subprocess.run(
                cmd,
                cwd=str(compiler_dir),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
                timeout=20,
            )

            print("Compiler output:")
            print(result.stdout)

            if result.returncode != 0:
                raise RuntimeError(
                    f"Compiler failed\noutput:\n{result.stdout}"
                )

            if not bt_file.exists():
                raise RuntimeError("Compiler exited successfully, but bt xml was not generated.")

            return bt_file.read_text(encoding="utf-8")

