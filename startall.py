import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent


def main():
    print("Running database migrations...")
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
        print(f"Database migration failed with exit code {migration.returncode}", file=sys.stderr)
        return migration.returncode

    print("Starting SrujanSetu server at http://127.0.0.1:5000 (http://localhost:5000)...")
    return subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "app.py")],
        cwd=PROJECT_ROOT,
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())