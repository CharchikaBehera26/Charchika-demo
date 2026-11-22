import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent


def main():
    migration = subprocess.run(
        [
            sys.executable,
            "-m",
            "flask",
            "--app",
            "app",
            "db",
            "upgrade",
        ],
        cwd=PROJECT_ROOT,
        check=False,
    )
    if migration.returncode:
        return migration.returncode

    return subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "app.py")],
        cwd=PROJECT_ROOT,
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
