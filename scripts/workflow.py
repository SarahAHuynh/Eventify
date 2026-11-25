"""Run Eventify turns in Herdr, or run the isolated single-Codex baseline."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import time

from validate import read_json, validate

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    "logistics": ("logistics.json", "logistics.md"),
    "budget": ("budget.json", "budget.md"),
    "marketing": ("marketing.md",),
    "reviewer": ("review.json",),
    "coordinator": ("event_package.md",),
}
SPECIALISTS = ("logistics", "budget", "marketing")
TIMEOUT = 600
DEFAULT_REVIEW_LIMIT = 3


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_suffix(".tmp")
    pending.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    pending.replace(path)


def free_model(model):
    return bool(re.fullmatch(r"opencode/[a-zA-Z0-9_.-]+-free", model))


def check_free_model(model):
    if not free_model(model):
        raise ValueError("Choose an opencode/<model>-free model.")
    listing = subprocess.run(["opencode", "models"], cwd=ROOT, capture_output=True,
                             text=True, timeout=30)
    if listing.returncode or model not in listing.stdout.splitlines():
        raise ValueError(f"Could not verify {model} in 'opencode models'.")


def rate_limited(path):
    with path.open(encoding="utf-8", errors="replace") as log:
        for line in log:
            try:
                event = json.loads(line)
            except ValueError:
                continue
            error = event.get("error") if isinstance(event, dict) else None
            if isinstance(error, dict) and (
                error.get("status") in (429, "429") or error.get("type") == "provider.free-limit"
            ):
                return True
    return False


def run_model(role, label, prompt, log_dir, cwd=ROOT, model="", reviewer_tool="opencode"):
    log_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.pop("OPENAI_API_KEY", None)
    env.pop("CODEX_API_KEY", None)
    if role == "marketing" or (role == "reviewer" and reviewer_tool == "opencode"):
        if not free_model(model):
            raise ValueError("Choose a currently free opencode/<model>-free model.")
        command = ["opencode", "run", "--model", model, "--format", "json", prompt]
    else:
        command = ["codex", "exec", "--sandbox", "workspace-write", "--json",
                   "--color", "never", "-"]
    print(f"{role}: {label} started", flush=True)
    log_path = log_dir / f"{label}.log"
    started = time.monotonic()
    result = {"role": role, "command": command[:-1], "started_utc": utc_now()}
    try:
        with log_path.open("x", encoding="utf-8") as log:
            (log_dir / f"{label}.prompt.md").write_text(prompt, encoding="utf-8")
            finished = subprocess.run(command, input=prompt if command[0] == "codex" else "",
                                      text=True, stdout=log, stderr=subprocess.STDOUT,
                                      cwd=cwd, env=env, timeout=TIMEOUT)
        if command[0] == "opencode" and rate_limited(log_path):
            result["failure_kind"] = "rate_limit"
            raise RuntimeError("OpenCode rate limit (HTTP 429). For a failed reviewer, "
                               "resume with --reviewer-tool codex or another verified free model.")
        if finished.returncode:
            raise RuntimeError(f"{command[0]} exited {finished.returncode}.")
        result["ok"] = True
    except FileExistsError:
        raise RuntimeError(f"Attempt log already exists: {log_path}.")
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        result.update(ok=False, error=str(exc))
    result["seconds"] = round(time.monotonic() - started, 2)
    save(log_dir / f"{label}.result.json", result)
    print(f"{role}: {label} {'finished' if result['ok'] else 'failed'}", flush=True)
    if not result["ok"]:
        raise RuntimeError(f"{label}: {result['error']} See {log_dir}.")


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def role_prompt(role, message):
    instructions = (ROOT / f"agents/{role}.md").read_text(encoding="utf-8")
    return f"{instructions}\n\n{message}\nUse files directly in the current repository."


def verify_files(paths):
    for path in paths:
        if path.suffix == ".json":
            read_json(path)
            continue
        if not path.is_file() or not path.read_text(encoding="utf-8").strip():
            raise RuntimeError(f"Missing or empty deliverable: {path}")


def worker(task_path, logs, model, reviewer_tool="opencode"):
    task = read_json(task_path)
    if task["status"] != "queued":
        raise RuntimeError(f"{task_path} is not queued.")
    task["status"] = "running"
    task["started_utc"] = utc_now()
    save(task_path, task)
    try:
        retry_instructions = task.get("review_retry_instructions", "")
        run_model(task["role"], task.get("attempt_label", task_path.stem), role_prompt(
            task["role"], f"Read {task_path} now. Execute only that assignment. "
            "Read its input dependencies and write all expected output files. "
            f"The Python runner updates task status after your turn.{retry_instructions}"
        ), logs, model=model, reviewer_tool=reviewer_tool)
        verify_files([ROOT / path for path in task["expected_outputs"]])
        task["status"] = "completed"
    except Exception as exc:
        task.update(status="failed", error=str(exc))
        raise
    finally:
        task["finished_utc"] = utc_now()
        save(task_path, task)


def run_in_pane(pane, command):
    action = f"Herdr pane run for {pane}"
    try:
        completed = subprocess.run(["herdr", "pane", "run", pane, command],
                                   cwd=ROOT, capture_output=True, text=True, timeout=20)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"{action} timed out. Inspect the pane for worker activity.") from exc
    except (OSError, UnicodeError) as exc:
        raise RuntimeError(f"{action} could not be confirmed ({type(exc).__name__}).") from exc
    if completed.returncode:
        raise RuntimeError(f"{action} exited with status {completed.returncode}. "
                           "Inspect the pane and Herdr logs.")
    # Herdr 0.9.5 acknowledges submission with a silent exit code zero.
    # The task file reports whether the worker actually completed.


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def findings_for_round(report, number, pending, passed):
    """Reject unsupported verdicts before the coordinator can assemble."""
    if type(report["round"]) is not int or report["round"] != number:
        raise ValueError("Wrong review round.")
    if not nonempty(report["summary"]):
        raise ValueError("Review needs a summary.")
    if not isinstance(report["findings"], list) or not isinstance(report["verified"], list):
        raise ValueError("Review findings and verified must be arrays.")
    findings = {}
    for item in report["findings"]:
        if not all(nonempty(item[key]) for key in ("id", "evidence", "impact", "request")):
            raise ValueError("Each finding needs an ID, evidence, impact, and request.")
        if item["role"] not in SPECIALISTS or item["id"] in findings:
            raise ValueError("Invalid finding role or duplicate ID.")
        findings[item["id"]] = item["role"]

    verified = set()
    for item in report["verified"]:
        identifier = item["id"]
        if not nonempty(identifier) or identifier not in pending:
            raise ValueError(f"Verification ID {identifier!r} is not outstanding in round {number}.")
        if identifier in verified:
            raise ValueError(f"Duplicate verification ID {identifier!r} in round {number}.")
        if not nonempty(item["evidence"]):
            raise ValueError(f"Verification ID {identifier!r} needs concrete evidence.")
        verified.add(identifier)
    for identifier, role in pending.items():
        if (identifier in verified) == (identifier in findings):
            raise ValueError(f"Review must verify or carry forward {identifier}.")
        if identifier in findings and findings[identifier] != role:
            raise ValueError(f"Review changed ownership of {identifier}.")

    if report["verdict"] == "revise" and findings:
        return findings
    if report["verdict"] == "approve" and number > 1 and passed and not findings:
        return {}
    raise ValueError("Review cannot advance: need actionable findings or a supported approval.")


class Workflow:
    def __init__(self, run_id, panes, model, reviewer_tool="opencode"):
        self.run_id = run_id
        self.tasks = ROOT / "tasks" / run_id
        self.outputs = ROOT / "outputs" / run_id
        self.reviews = ROOT / "reviews" / run_id
        self.logs = ROOT / "logs" / run_id
        self.panes = panes
        self.model = model
        self.reviewer_tool = reviewer_tool
        self.review_limit = DEFAULT_REVIEW_LIMIT
        self.active = {}
        self.revisions = dict.fromkeys(FILES, 0)

    def assign(self, roles, dependencies, context):
        contracts = {}
        for role in roles:
            self.revisions[role] += 1
            revision = self.revisions[role]
            path = self.tasks / f"{role}-r{revision}.json"
            directory = (self.reviews if role == "reviewer" else self.outputs) / f"{role}-r{revision}"
            directory.mkdir(parents=True, exist_ok=False)
            contract = {
                "role": role,
                "revision": revision,
                "status": "queued",
                "dependencies": ["inputs/client_request.md", "inputs/price_catalog.csv",
                                 "inputs/output_formats.md", *dependencies[role]],
                "expected_outputs": [str((directory / name).relative_to(ROOT)) for name in FILES[role]],
            }
            contracts[path] = contract
        payload = {str(path.relative_to(ROOT)): contract for path, contract in contracts.items()}
        label = "assign-" + "-".join(path.stem for path in contracts)
        run_model("coordinator", label, role_prompt("coordinator",
            f"{context}\nRead the dependencies before drafting the assignments. "
            "Save one JSON task object at each path below. Copy all metadata exactly "
            "and add an instructions string and a nonempty acceptance_criteria list of strings. "
            "Write only these task files during this turn.\n" + json.dumps(payload, indent=2)
        ), self.logs)
        for path, contract in contracts.items():
            try:
                task = read_json(path)
            except (OSError, ValueError) as exc:
                raise RuntimeError(f"Invalid coordinator assignment: {exc}. "
                                   f"See {self.logs / (label + '.log')}.") from exc
            criteria = task.get("acceptance_criteria")
            if (any(task.get(key) != value for key, value in contract.items())
                    or type(task["revision"]) is not int
                    or not nonempty(task.get("instructions"))
                    or not isinstance(criteria, list) or not criteria
                    or not all(nonempty(entry) for entry in criteria)):
                raise RuntimeError(f"Invalid coordinator assignment: {path}.")
        return list(contracts)

    def dispatch(self, path):
        task = read_json(path)
        role = task["role"]
        if role == "coordinator":
            worker(path, self.logs, self.model)
            return
        command = ["python3", "scripts/workflow.py", "worker",
                   str(path), str(self.logs), self.model]
        if role == "reviewer":
            command.extend(["--reviewer-tool", self.reviewer_tool])
        run_in_pane(self.panes[role], shlex.join(command))
        deadline = time.monotonic() + TIMEOUT + 30
        while time.monotonic() < deadline:
            task = read_json(path)
            if task["status"] == "completed":
                return
            if task["status"] == "failed":
                raise RuntimeError(f"{role}: {task['error']}")
            time.sleep(1)
        raise RuntimeError(f"Timed out waiting for {role}. Inspect its pane and logs.")

    def deliver(self, roles, dependencies, context):
        paths = self.assign(roles, dependencies, context)
        with ThreadPoolExecutor(max_workers=len(paths)) as pool:
            list(pool.map(self.dispatch, paths))
        for path in paths:
            task = read_json(path)
            self.active[task["role"]] = task["expected_outputs"]

    def revise(self, pending, report, report_path, validation_path, targeted=False):
        changed = set(pending.values())
        before = {}
        for role in changed:
            before[role] = [hashlib.sha256((ROOT / p).read_bytes()).digest()
                            for p in self.active[role]]
        if "logistics" in changed:
            dependencies = [*self.active["logistics"], report_path, validation_path]
            context = "Route the reviewer findings for logistics and specify the requested changes."
            if targeted:
                dependencies.extend(self.active["budget"])
                context += (
                    " Limit edits to the findings and necessary consistency changes. Point the "
                    "shortage link at the retained Budget r3 procedure, preserve the previously "
                    "verified opening desk handoff and replenishment authority, and keep the "
                    "schedule and supply quantities. For these Markdown-only changes, carry "
                    "forward logistics.json byte-for-byte at the new revision path. Specify "
                    "desk and written-update coverage for V2's absence while preserving V4's "
                    "access duties."
                )
            self.deliver(["logistics"], {"logistics": dependencies}, context)
            if not targeted:
                changed.update(("budget", "marketing"))
        downstream = [role for role in ("budget", "marketing") if role in changed]
        if downstream:
            context = (
                "Route each role's applicable findings and reconcile them with current logistics. "
                "Limit edits to those findings and necessary consistency changes. For Marketing, "
                "describe the step-free route as planned pending verification in all three pieces, "
                "say where verified information will be shared, and retain the accommodation contact."
                if targeted else
                "Route each role's applicable reviewer findings and require reconciliation "
                "with current logistics. If a role has no finding, assign a dependency refresh."
            )
            self.deliver(downstream, {
                role: [*self.active["logistics"], *self.active[role],
                       report_path, validation_path] for role in downstream
            }, context)
        for role, original in before.items():
            current = [hashlib.sha256((ROOT / p).read_bytes()).digest() for p in self.active[role]]
            if original == current:
                raise RuntimeError(f"{role} saved an unchanged revision. See {report['summary']}")

    def execute(self):
        self.deliver(["logistics"], {"logistics": []}, "Assign the first logistics draft.")
        self.deliver(["budget", "marketing"], {
            role: self.active["logistics"] for role in ("budget", "marketing")
        }, "Assign independent budget and marketing drafts based on logistics.")
        return self.review(1, {}, [])

    def review(self, first_round, pending, history, retry=None):
        for number in range(first_round, self.review_limit + 1):
            evidence = [path for role in SPECIALISTS for path in self.active[role]]
            validation_path = self.reviews / f"validation-r{number}.json"
            validation_ref = str(validation_path.relative_to(ROOT))
            if retry is None:
                report = validate(ROOT / self.active["logistics"][0], ROOT / self.active["budget"][0])
                save(validation_path, report)
                [review_task] = self.assign(
                    ["reviewer"], {"reviewer": [*evidence, validation_ref, *history]},
                    f"Assign independent QA round {number}. Have QA verify outstanding "
                    "findings against old and new files. Instruct QA to account for these "
                    f"outstanding IDs exactly once across findings and verified: {sorted(pending)}. "
                    "Check for regressions in previously accepted verifications and discuss "
                    "those checks in the summary. "
                    "Round one must identify an "
                    "evidence-based improvement. "
                    f"The authorized round limit is {self.review_limit}. Specify the "
                    f"current specialist artifacts: {evidence}. Current validation: "
                    f"{validation_ref}. The remaining dependencies are historical.")
            else:
                review_task, retry = retry, None
                report = read_json(validation_path)
            save(self.review_checkpoint(number),
                 {"round": number, "pending": pending, "history": history})
            self.dispatch(review_task)
            [review_path] = read_json(review_task)["expected_outputs"]
            review = read_json(ROOT / review_path)
            pending = findings_for_round(review, number, pending, report["passed"])
            if review["verdict"] == "approve":
                self.deliver(["coordinator"], {
                    "coordinator": [*evidence, validation_ref, review_path]
                }, "Assign assembly of the approved event package with links to its evidence.")
                return {"status": "approved", "package": self.active["coordinator"][0],
                        "review_rounds": number}
            if number == self.review_limit:
                raise RuntimeError(f"Review limit reached with open findings {sorted(pending)}. "
                                   f"See {review_path} and {validation_ref}.")
            history.extend(p for p in [*evidence, validation_ref, review_path] if p not in history)
            self.revise(pending, review, review_path, validation_ref)

    def review_checkpoint(self, number):
        name = "review-checkpoint-r4.json" if number == 4 else "review-checkpoint.json"
        return self.logs / name

    def saved_review(self, checkpoint, limit):
        # Original runs have no checkpoint and can only retry a failed first review turn.
        state = (read_json(checkpoint) if checkpoint.exists()
                 else {"round": 1, "pending": {}, "history": []})
        number = state["round"]
        if type(number) is not int or not 1 <= number <= limit:
            raise ValueError("Invalid saved review round.")
        retry = self.tasks / f"reviewer-r{number}.json"
        for path in self.tasks.glob("*.json"):
            task = read_json(path)
            role, revision = task["role"], task["revision"]
            allowed_statuses = ("completed",)
            if path == retry:
                allowed_statuses = ("failed", "completed") if checkpoint.exists() else ("failed",)
            if (role not in FILES or type(revision) is not int or revision < 1
                    or path.stem != f"{role}-r{revision}" or task["status"] not in allowed_statuses
                    or role == "coordinator" or (role == "reviewer" and revision > number)):
                raise ValueError(f"Cannot resume from task state in {path}.")
            directory = (self.reviews if role == "reviewer" else self.outputs) / path.stem
            expected = [str((directory / name).relative_to(ROOT)) for name in FILES[role]]
            if task["expected_outputs"] != expected:
                raise ValueError(f"Unexpected output paths in {path}.")
            if path != retry:
                verify_files([ROOT / name for name in expected])
            if revision > self.revisions[role]:
                self.revisions[role] = revision
                self.active[role] = task["expected_outputs"]
        task = read_json(retry)
        evidence = [name for role in SPECIALISTS for name in self.active[role]]
        validation = self.reviews / f"validation-r{number}.json"
        read_json(validation)
        required = {*evidence, str(validation.relative_to(ROOT)), *state["history"]}
        if not required.issubset(task["dependencies"]):
            raise ValueError("Saved review does not match the current evidence.")
        return retry, task, state, evidence, validation

    def retryable_review(self):
        checkpoint = self.review_checkpoint(self.review_limit)
        retry, task, state, _, validation = self.saved_review(checkpoint, self.review_limit)
        rejection = None
        if task["status"] == "completed":
            [output] = task["expected_outputs"]
            passed = read_json(validation)["passed"]
            try:
                findings_for_round(read_json(ROOT / output), state["round"], state["pending"], passed)
            except (ValueError, TypeError, KeyError) as exc:
                rejection = str(exc)
            else:
                raise ValueError("Saved review passed the review protocol and cannot be retried.")
        return retry, task, state, rejection

    def prepare_round_four(self):
        _, task, state, evidence, validation = self.saved_review(
            self.review_checkpoint(DEFAULT_REVIEW_LIMIT), DEFAULT_REVIEW_LIMIT
        )
        if state["round"] != DEFAULT_REVIEW_LIMIT or task["status"] != "completed":
            raise ValueError("Round four requires a completed round-three review.")
        [review_path] = task["expected_outputs"]
        report = read_json(ROOT / review_path)
        validation_path = str(validation.relative_to(ROOT))
        pending = findings_for_round(
            report, state["round"], state["pending"], read_json(validation)["passed"]
        )
        if not pending:
            raise ValueError("Round four requires an accepted round-three report with open findings.")
        history = list(dict.fromkeys([*state["history"], *evidence, validation_path, review_path]))

        def continue_to_review():
            self.revise(pending, report, review_path, validation_path, targeted=True)
            return self.review(4, pending, history)

        return pending, continue_to_review


def check_workspace(model, panes):
    if os.environ.get("HERDR_ENV") != "1" or not free_model(model):
        raise ValueError("Run inside Herdr with a verified opencode/<model>-free model.")
    workspace = os.environ.get("HERDR_WORKSPACE_ID", "")
    coordinator = os.environ.get("HERDR_PANE_ID", "")
    if (set(panes) != {*SPECIALISTS, "reviewer"}
            or not workspace or not coordinator.startswith(workspace + ":")
            or any(not pane.startswith(workspace + ":") for pane in panes.values())
            or len({coordinator, *panes.values()}) != 5):
        raise ValueError("Use five distinct panes in one Herdr workspace.")


def start(run_id, model, panes):
    check_workspace(model, panes)
    check_codex_login()
    workflow = Workflow(run_id, panes, model)
    workflow.tasks.mkdir(exist_ok=False)
    summary = {"run": run_id, "started_utc": utc_now(), "opencode_model": model, "panes": panes}
    return record_run(workflow, summary, workflow.execute)


def record_run(workflow, summary, execute):
    started = time.monotonic()
    for field in ("status", "error", "seconds"):
        summary.pop(field, None)
    save(workflow.logs / "run.json", {**summary, "status": "running"})
    try:
        summary.update(execute())
    except (OSError, ValueError, TypeError, RuntimeError, KeyError, subprocess.SubprocessError) as exc:
        summary.update(status="unresolved", error=str(exc))
    summary["seconds"] = round(time.monotonic() - started, 2)
    save(workflow.logs / "run.json", summary)
    print(json.dumps(summary, indent=2))
    return int(summary["status"] != "approved")


def resume(run_id, model=None, reviewer_tool=None, authorize_round_four=False):
    if authorize_round_four and run_id != "demo-02":
        raise ValueError("--authorize-round-four is available only for demo-02.")
    logs = ROOT / "logs" / run_id
    with (logs / "resume.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("This run already has an active resume.") from exc
        summary = read_json(logs / "run.json")
        if summary["status"] != "unresolved":
            raise ValueError("Only unresolved runs can be resumed.")
        previous_tool = summary.get("reviewer_tool", "opencode")
        previous_model = summary["opencode_model"]
        reviewer_tool = reviewer_tool or ("opencode" if model else previous_tool)
        if model and reviewer_tool == "codex":
            raise ValueError("--model selects an OpenCode model and requires an OpenCode reviewer.")
        model = model or previous_model
        check_workspace(model, summary["panes"])
        workflow = Workflow(run_id, summary["panes"], model, reviewer_tool)
        if authorize_round_four:
            workflow.review_limit = 4
        new_round_four = authorize_round_four and not workflow.review_checkpoint(4).exists()
        if new_round_four:
            pending, continue_to_review = workflow.prepare_round_four()
        else:
            retry, task, state, rejection = workflow.retryable_review()
        if reviewer_tool == "opencode":
            check_free_model(model)
        check_codex_login()
        if new_round_four:
            summary["round_four_authorization"] = {
                "started_utc": utc_now(),
                "previous_error": summary["error"],
                "findings": pending,
                "reviewer_tool": reviewer_tool,
            }
            summary["reviewer_tool"] = reviewer_tool
            summary["opencode_model"] = model
            return record_run(workflow, summary, continue_to_review)

        previous_label = task.get("attempt_label", retry.stem)
        previous_log = logs / f"{previous_label}.log"
        attempts = summary.setdefault("resumes", [])
        label = f"{retry.stem}-retry{len(attempts) + 1}"
        failure_kind = "review_protocol" if rejection is not None else (
            "rate_limit" if previous_tool == "opencode" and previous_log.exists()
            and rate_limited(previous_log) else "error"
        )
        attempts.append({
            "started_utc": utc_now(),
            "previous_reviewer_tool": previous_tool,
            "reviewer_tool": reviewer_tool,
            "previous_model": previous_model if previous_tool == "opencode" else None,
            "model": model if reviewer_tool == "opencode" else None,
            "previous_attempt": previous_label,
            "previous_error": rejection if rejection is not None else task["error"],
            "previous_failure_kind": failure_kind,
            "attempt": label,
        })
        summary["reviewer_tool"] = reviewer_tool
        summary["opencode_model"] = model

        def continue_review():
            [output] = task["expected_outputs"]
            path = ROOT / output
            if path.exists():
                suffix = "rejected-review" if rejection is not None else "partial-review"
                archive = logs / f"{previous_label}.{suffix}.json"
                if archive.exists():
                    raise FileExistsError(f"Review archive already exists: {archive}")
                path.rename(archive)
                if rejection is not None:
                    task["review_retry_instructions"] = (
                        f"\nThis is a protocol retry of round {state['round']}. "
                        "The runner rejected the previous report. "
                        f"Read {archive.relative_to(ROOT)} and independently reassess its findings "
                        "against the unchanged artifacts. "
                        f"The only outstanding IDs are {sorted(state['pending'])}. "
                        "Account for each once, in verified with concrete old and current evidence "
                        "if resolved, or in findings if unresolved. Use this saved list for ID "
                        "accounting if the task's acceptance criteria list more prior IDs. "
                        "Discuss earlier accepted resolutions in the summary if relevant. "
                        "Report any material issues in findings and apply all approval criteria."
                    )
            for field in ("started_utc", "finished_utc", "error"):
                task.pop(field, None)
            save(retry, {**task, "status": "queued", "attempt_label": label})
            return workflow.review(state["round"], state["pending"], state["history"], retry)

        return record_run(workflow, summary, continue_review)


def check_codex_login():
    login = subprocess.run(["codex", "login", "status"], capture_output=True, text=True, timeout=20)
    if login.returncode or "Logged in using ChatGPT" not in login.stdout + login.stderr:
        raise RuntimeError("Codex must be logged in using ChatGPT.")


def baseline(run_id):
    check_codex_login()
    directory = ROOT / "baseline" / "runs" / run_id
    directory.mkdir(parents=True, exist_ok=False)
    for source in ("client_request.md", "price_catalog.csv", "output_formats.md"):
        (directory / "inputs").mkdir(exist_ok=True)
        shutil.copyfile(ROOT / "inputs" / source, directory / "inputs" / source)
    # A separate Git root prevents project-level role instructions from being inherited.
    subprocess.run(["git", "init", "-q", str(directory)], check=True)
    prompt = (ROOT / "baseline/prompt.md").read_text(encoding="utf-8")
    started = time.monotonic()
    report = {"status": "completed"}
    try:
        run_model("baseline", "single", prompt, directory / "logs", cwd=directory)
        verify_files([directory / "deliverables" / name for role in (*SPECIALISTS, "coordinator")
                      for name in FILES[role]])
    except (OSError, RuntimeError) as exc:
        report.update(status="unresolved", error=str(exc))
    report["seconds"] = round(time.monotonic() - started, 2)
    report["validation"] = validate(directory / "deliverables/logistics.json",
                                    directory / "deliverables/budget.json",
                                    directory / "inputs/price_catalog.csv")
    save(directory / "result.json", report)
    print(json.dumps(report, indent=2))
    return int(report["status"] != "completed" or not report["validation"]["passed"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    live = commands.add_parser("start", help="Run from the coordinator's Herdr pane.")
    live.add_argument("run_id")
    live.add_argument("model")
    for role in (*SPECIALISTS, "reviewer"):
        live.add_argument(role)
    continuation = commands.add_parser("resume", help="Retry a failed review in its original Herdr workspace.")
    continuation.add_argument("run_id")
    continuation.add_argument("--model", help="Use a different verified free OpenCode model.")
    continuation.add_argument("--reviewer-tool", choices=("opencode", "codex"),
                              help="Select the reviewer CLI. Defaults to the last reviewer tool.")
    continuation.add_argument("--authorize-round-four", action="store_true",
                              help="Authorize a final fourth review round for demo-02 only.")
    job = commands.add_parser("worker", help="Internal command dispatched by the coordinator.")
    job.add_argument("task", type=Path)
    job.add_argument("logs", type=Path)
    job.add_argument("model")
    job.add_argument("--reviewer-tool", choices=("opencode", "codex"), default="opencode")
    single = commands.add_parser("baseline", help="Run one isolated Codex prompt.")
    single.add_argument("run_id")
    args = parser.parse_args()
    if args.command == "worker":
        try:
            worker(args.task, args.logs, args.model, args.reviewer_tool)
        except (OSError, ValueError, RuntimeError) as exc:
            parser.exit(1, f"Worker {args.task}: {exc}\n")
        return 0
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", args.run_id):
        parser.error("Run ID must contain only letters, digits, underscores, and hyphens.")
    if args.command == "baseline":
        return baseline(args.run_id)
    if args.command == "resume":
        try:
            return resume(args.run_id, args.model, args.reviewer_tool, args.authorize_round_four)
        except (OSError, ValueError, TypeError, RuntimeError, KeyError, subprocess.SubprocessError) as exc:
            parser.exit(1, f"Resume {args.run_id}: {exc}\n")
    panes = {role: getattr(args, role) for role in (*SPECIALISTS, "reviewer")}
    return start(args.run_id, args.model, panes)


if __name__ == "__main__":
    raise SystemExit(main())
