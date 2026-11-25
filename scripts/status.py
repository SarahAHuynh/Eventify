"""Read Eventify task states without launching any agents."""
import argparse
from pathlib import Path

from validate import read_json

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_id", nargs="?")
    args = parser.parse_args()
    runs = sorted(path for path in (ROOT / "tasks").iterdir() if path.is_dir())
    if args.run_id:
        runs = [path for path in runs if path.name == args.run_id]
    if not runs:
        print("No matching Eventify runs.")
        return
    for run in runs:
        logs = ROOT / "logs" / run.name
        summary = logs / "run.json"
        if not summary.exists():
            summary = logs / "run.public.json"
        state = read_json(summary) if summary.exists() else {"status": "starting"}
        print(f"{run.name}: {state['status']}")
        for field in ("package", "error"):
            if field in state:
                print(f"  {state[field]}")
        for path in sorted(run.glob("*.json")):
            try:
                task_status = read_json(path).get("status", "unknown")
            except (OSError, ValueError, AttributeError):
                task_status = "unreadable"
            print(f"  {path.stem:<18} {task_status}")


if __name__ == "__main__":
    main()
