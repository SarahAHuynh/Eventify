"""Validation fixtures are synthetic tests, never experiment results."""
import json
from pathlib import Path
import shlex
from subprocess import CompletedProcess, TimeoutExpired
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from validate import ACTIVITIES, read_json, validate
from workflow import (
    Workflow, check_free_model, findings_for_round, free_model, record_run, resume,
    run_in_pane, run_model, save, worker,
)


def sample_plan():
    times = ["16:00", "16:30", "17:00", "17:30", "18:00", "18:30", "19:00"]
    return {"agenda": [
        {"activity": activity, "start": times[i], "end": times[i + 1],
         "volunteers": ["V1", "V2"]}
        for i, activity in enumerate(ACTIVITIES)
    ]}


def sample_budget():
    return {
        "items": [
            {"sku": "FRUIT10", "quantity": 5, "unit_cents": 1000, "total_cents": 5000},
            {"sku": "WATER24", "quantity": 3, "unit_cents": 800, "total_cents": 2400},
            {"sku": "TAG25", "quantity": 2, "unit_cents": 450, "total_cents": 900},
        ],
        "subtotal_cents": 8300, "reserve_cents": 3000, "total_cents": 11300,
    }


class ValidationTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.plan_path = Path(temp.name) / "logistics.json"
        self.budget_path = Path(temp.name) / "budget.json"
        self.plan = sample_plan()
        self.budget = sample_budget()

    def report(self):
        self.plan_path.write_text(json.dumps(self.plan))
        self.budget_path.write_text(json.dumps(self.budget))
        return validate(self.plan_path, self.budget_path)

    def test_valid_schedule_and_budget(self):
        self.assertEqual(self.report(), {"passed": True, "errors": []})

    def test_gap_overlap_and_end(self):
        self.plan["agenda"][1]["start"] = "16:35"
        self.plan["agenda"][2]["start"] = "16:55"
        self.plan["agenda"][-1]["end"] = "18:59"
        errors = self.report()["errors"]
        self.assertEqual(len(errors), 3)

    def test_missing_activity(self):
        self.plan["agenda"].pop()
        self.assertFalse(self.report()["passed"])

    def test_wrong_volunteer_ids_and_duplicates(self):
        for ids in (["V7"], ["V1", "V1"], []):
            with self.subTest(ids=ids):
                self.plan["agenda"][0]["volunteers"] = ids
                self.assertIn("distinct volunteers", " ".join(self.report()["errors"]))

    def test_wrong_prices_and_arithmetic(self):
        self.budget["items"][0].update(unit_cents=900, total_cents=4500)
        self.budget.update(subtotal_cents=7800, total_cents=10800)
        errors = self.report()["errors"]
        self.assertEqual(len(errors), 4)

    def test_attendance_shortfall_by_category(self):
        for row in self.budget["items"]:
            row["quantity"] -= 1
        errors = " ".join(self.report()["errors"])
        for expected in ("food: covers 40", "drink: covers 48", "name_tags: covers 25"):
            self.assertIn(expected, errors)

    def test_unknown_duplicate_and_non_integer(self):
        self.budget["items"].append(self.budget["items"][0].copy())
        self.budget["items"].append({"sku": "MISSING", "quantity": 1})
        self.budget["items"][1]["quantity"] = True
        errors = " ".join(self.report()["errors"])
        for expected in ("duplicated SKU: 'FRUIT10'", "'MISSING'", "positive whole number"):
            self.assertIn(expected, errors)

    def test_reserve_and_maximum(self):
        self.budget["reserve_cents"] = 2999
        self.assertIn("at least 3000", " ".join(self.report()["errors"]))
        self.budget["reserve_cents"] = 25000
        self.assertIn("exceeds 30000", " ".join(self.report()["errors"]))

    def test_bad_json_and_missing_file(self):
        self.plan_path.write_text("bad JSON")
        errors = validate(self.plan_path, self.budget_path)["errors"]
        self.assertEqual(len(errors), 2)


def finding():
    return {"id": "M1", "role": "marketing", "evidence": "Fixture omits the hours.",
            "impact": "Attendees cannot plan.", "request": "Add the hours."}


def review(number, verdict, findings=(), verified=()):
    return {"round": number, "verdict": verdict, "summary": "Fixture QA.",
            "findings": list(findings), "verified": list(verified)}


class ReviewTests(unittest.TestCase):
    def test_round_three_rejects_reverification_of_a_closed_id(self):
        first = findings_for_round(review(1, "revise", [finding()]), 1, {}, True)
        followup = {**finding(), "id": "M2"}
        earlier = {"id": "M1", "evidence": "Round two documents the correction."}
        pending = findings_for_round(review(2, "revise", [followup], [earlier]), 2, first, True)
        with self.assertRaisesRegex(ValueError, "Verification ID 'M1' is not outstanding in round 3"):
            findings_for_round(review(3, "revise", [followup], [earlier]), 3, pending, True)
        self.assertEqual(findings_for_round(review(3, "revise", [followup]), 3, pending, True),
                         {"M2": "marketing"})

    def test_outstanding_verification_needs_evidence_and_must_be_unique(self):
        pending = {"M1": "marketing"}
        blank = {"id": "M1", "evidence": "  "}
        verified = {"id": "M1", "evidence": "Hours added."}
        with self.assertRaisesRegex(ValueError, "needs concrete evidence"):
            findings_for_round(review(2, "approve", verified=[blank]), 2, pending, True)
        with self.assertRaisesRegex(ValueError, "Duplicate verification ID"):
            findings_for_round(review(2, "approve", verified=[verified, verified]), 2, pending, True)

    def test_first_round_has_to_request_a_revision(self):
        with self.assertRaises(ValueError):
            findings_for_round(review(1, "approve"), 1, {}, True)
        self.assertEqual(findings_for_round(review(1, "revise", [finding()]), 1, {}, True),
                         {"M1": "marketing"})

    def test_cannot_approve_before_verification_or_with_validation_errors(self):
        pending = {"M1": "marketing"}
        with self.assertRaises(ValueError):
            findings_for_round(review(2, "approve"), 2, pending, True)
        approved = review(2, "approve", verified=[{"id": "M1", "evidence": "Hours added."}])
        with self.assertRaises(ValueError):
            findings_for_round(approved, 2, pending, False)
        self.assertEqual(findings_for_round(approved, 2, pending, True), {})

    def test_free_model_requires_explicit_free_provider_id(self):
        self.assertTrue(free_model("opencode/test-free"))
        self.assertFalse(free_model("other/test-free"))
        self.assertFalse(free_model("opencode/test"))


class WorkflowTests(unittest.TestCase):
    def test_pane_run_reports_rejection_without_dumping_cli_output(self):
        with patch("workflow.subprocess.run", return_value=CompletedProcess([], 1, "", "")):
            with self.assertRaisesRegex(RuntimeError, "Herdr pane run for w5:p2.*status 1"):
                run_in_pane("w5:p2", "worker command")

    def test_pane_run_timeout_does_not_resubmit(self):
        with patch("workflow.subprocess.run", side_effect=TimeoutExpired("herdr", 20)) as run:
            with self.assertRaisesRegex(RuntimeError, "Herdr pane run for w5:p2 timed out"):
                run_in_pane("w5:p2", "worker command")
            run.assert_called_once()

    def test_json_file_errors_name_the_artifact(self):
        with TemporaryDirectory() as name:
            path = Path(name) / "logistics-r1.json"
            with self.assertRaisesRegex(FileNotFoundError, "logistics-r1.json.*missing"):
                read_json(path)
            for data, message in ((b" \n", "empty"), (b"{", "invalid JSON at line 1"),
                                  (b"[]", "expected a JSON object"), (b"\xff", "UTF-8")):
                with self.subTest(data=data):
                    path.write_bytes(data)
                    with self.assertRaisesRegex(ValueError, f"logistics-r1.json.*{message}"):
                        read_json(path)

    def test_worker_records_malformed_json_output_as_failed(self):
        with TemporaryDirectory() as name, patch("workflow.ROOT", Path(name)):
            root = Path(name)
            path = root / "logistics-r1.json"
            save(path, {"role": "logistics", "status": "queued",
                        "expected_outputs": ["logistics.json"]})
            (root / "logistics.json").write_text("{", encoding="utf-8")
            with patch("workflow.run_model"), patch("workflow.role_prompt"):
                with self.assertRaisesRegex(ValueError, "logistics.json.*invalid JSON"):
                    worker(path, root / "logs", "")
            task = read_json(path)
            self.assertEqual(task["status"], "failed")
            self.assertIn("logistics.json", task["error"])

    def test_mocked_dispatch_revision_and_approval(self):
        self.exercise_workflow(approve=True)

    def test_stops_after_three_rounds_with_open_findings(self):
        self.exercise_workflow(approve=False)

    def test_resume_legacy_review_then_later_review_without_replaying_work(self):
        self.exercise_workflow(approve=True, retry_reviews=True)

    def test_resume_with_codex_in_original_reviewer_pane_through_approval(self):
        self.exercise_workflow(approve=True, retry_reviews=True, reviewer_tool="codex")

    def test_retry_rejected_round_three_preserves_history_and_honors_round_limit(self):
        self.exercise_workflow(approve=False, reject_final_report=True)

    def test_retry_rejected_final_review_can_assemble_after_valid_approval(self):
        self.exercise_workflow(approve=True, reject_final_report=True)

    def test_authorized_round_four_revises_only_affected_roles_and_assembles_on_approval(self):
        self.exercise_workflow(approve=True, round_four=True)

    def test_authorized_round_four_stops_with_open_findings(self):
        self.exercise_workflow(approve=False, round_four=True)

    def test_round_four_flag_is_restricted_to_demo_02(self):
        with self.assertRaisesRegex(ValueError, "only for demo-02"):
            resume("another-run", authorize_round_four=True)

    def test_codex_reviewer_uses_stdin_and_marketing_uses_opencode(self):
        with TemporaryDirectory() as name, patch("workflow.subprocess.run",
                return_value=CompletedProcess([], 0)) as launch:
            logs = Path(name)
            run_model("reviewer", "reviewer-r1", "QA", logs, reviewer_tool="codex")
            command, = launch.call_args.args
            self.assertEqual(command[:2], ["codex", "exec"])
            self.assertEqual(launch.call_args.kwargs["input"], "QA")
            run_model("marketing", "marketing-r2", "Revise", logs,
                      model="opencode/test-free", reviewer_tool="codex")
            command, = launch.call_args.args
            self.assertEqual(command[:4], ["opencode", "run", "--model", "opencode/test-free"])

    def test_opencode_rate_limit_is_logged_even_with_zero_exit_status(self):
        with TemporaryDirectory() as name:
            logs = Path(name)

            def limited(command, *, stdout, **kwargs):
                self.assertEqual(command[:4], ["opencode", "run", "--model", "opencode/test-free"])
                stdout.write('{"type":"error","error":{"type":"provider.free-limit","status":429}}\n')
                return CompletedProcess(command, 0)

            with patch("workflow.subprocess.run", side_effect=limited) as launch:
                with self.assertRaisesRegex(RuntimeError, "HTTP 429"):
                    run_model("reviewer", "reviewer-r1", "QA", logs, model="opencode/test-free")
            launch.assert_called_once()
            result = read_json(logs / "reviewer-r1.result.json")
            self.assertFalse(result["ok"])
            self.assertEqual(result["failure_kind"], "rate_limit")

    def test_resume_model_must_be_free_and_listed(self):
        with patch("workflow.subprocess.run", return_value=CompletedProcess(
            ["opencode", "models"], 0, stdout="opencode/current-free\nopencode/paid\n"
        )) as listing:
            check_free_model("opencode/current-free")
            with self.assertRaisesRegex(ValueError, "Could not verify"):
                check_free_model("opencode/missing-free")
            with self.assertRaisesRegex(ValueError, "Choose"):
                check_free_model("opencode/paid")
        self.assertEqual(listing.call_count, 2)

    def exercise_workflow(self, approve, retry_reviews=False, reviewer_tool="opencode",
                          reject_final_report=False, round_four=False):
        with TemporaryDirectory() as name, patch("workflow.ROOT", Path(name)):
            root = Path(name)
            (root / "tasks").mkdir()
            roles = ("logistics", "budget", "marketing", "reviewer")
            panes = {role: f"w6:p{index}" for index, role in enumerate(roles, 2)}
            run = Workflow("demo-02" if round_four else "fixture", panes, "opencode/test-free")
            failed = set()
            turns = []
            review_tools = []
            logistics_finding = {**finding(), "id": "L1", "role": "logistics"}

            def fake_coordinator(role, label, prompt, *args):
                self.assertEqual(role, "coordinator")
                contracts = json.loads(prompt[prompt.index("\n{") + 1:])
                for path, task in contracts.items():
                    save(root / path, {**task, "instructions": "Fixture assignment.",
                                       "acceptance_criteria": ["Fixture criterion."]})

            def fake_subprocess(args, **kwargs):
                cli, group, action, pane, command = args
                self.assertEqual((cli, group, action), ("herdr", "pane", "run"))
                _, _, _, task_path, _, model, *options = shlex.split(command)
                path = Path(task_path)
                task = json.loads(path.read_text())
                self.assertEqual(pane, panes[task["role"]])
                if task["role"] == "reviewer":
                    self.assertEqual(options[:1], ["--reviewer-tool"])
                    review_tools.append(options[1])
                else:
                    self.assertEqual(options, [])
                fake_worker(path, None, model)
                return CompletedProcess(args, 0, stdout="", stderr="")

            def fake_worker(path, logs, model):
                task = json.loads(path.read_text())
                role, revision = task["role"], task["revision"]
                turns.append((path.stem, model))
                if retry_reviews and role == "reviewer" and revision not in failed:
                    failed.add(revision)
                    (run.logs / f"{path.stem}.log").write_text(
                        '{"error":{"type":"provider.free-limit","status":429}}\n'
                    )
                    save(path, {**task, "status": "failed", "error": "HTTP 429"})
                    return
                dependencies = task["dependencies"]
                if role in ("budget", "marketing"):
                    self.assertTrue(any(p.endswith("logistics.json") for p in dependencies))
                if role == "marketing" and revision == 2:
                    self.assertTrue(any(p.endswith("reviewer-r1/review.json") for p in dependencies))
                if round_four and revision == 4:
                    self.assertTrue(any(p.endswith("reviewer-r3/review.json") for p in dependencies))
                    if role in ("logistics", "reviewer"):
                        self.assertTrue(any(p.endswith("budget-r3/budget.md") for p in dependencies))
                    if role in ("marketing", "reviewer"):
                        self.assertTrue(any(p.endswith("logistics-r4/logistics.md") for p in dependencies))
                for relative in task["expected_outputs"]:
                    output = root / relative
                    if output.name == "logistics.json":
                        save(output, sample_plan())
                    elif output.name == "budget.json":
                        save(output, sample_budget())
                    elif role == "reviewer":
                        report = (review(revision, "revise", [finding()])
                                  if revision == 1 or not approve or reject_final_report or round_four
                                  else review(2, "approve", verified=[
                                      {"id": "M1", "evidence": "Fixture contains hours."}
                                  ]))
                        if reject_final_report and revision == 3:
                            if "attempt_label" not in task:
                                report["verified"] = [{"id": "closed", "evidence": "Earlier fix."}]
                            else:
                                instructions = task["review_retry_instructions"]
                                self.assertIn("The only outstanding IDs are ['M1']", instructions)
                                self.assertIn("reviewer-r3.rejected-review.json", instructions)
                                if approve:
                                    report = review(3, "approve", verified=[
                                        {"id": "M1", "evidence": "Fixture contains hours."}
                                    ])
                        if round_four:
                            report = (review(4, "approve", verified=[
                                {"id": identifier, "evidence": "Current and previous fixture compared."}
                                for identifier in ("M1", "L1")
                            ]) if revision == 4 and approve
                                else review(revision, "revise", [finding(), logistics_finding]))
                        save(output, report)
                    else:
                        output.write_text(f"Fixture {role} draft {revision}.")
                save(path, {**task, "status": "completed"})

            with patch("workflow.run_model", side_effect=fake_coordinator), \
                    patch("workflow.subprocess.run", side_effect=fake_subprocess), \
                    patch("workflow.worker", side_effect=fake_worker), \
                    patch("workflow.role_prompt", side_effect=lambda role, prompt: prompt):
                if round_four:
                    run.tasks.mkdir()
                    summary_path = run.logs / "run.json"
                    summary_data = {"run": run.run_id, "opencode_model": run.model, "panes": panes}
                    self.assertEqual(record_run(run, summary_data, run.execute), 1)
                    prior_error = read_json(summary_path)["error"]
                    self.assertIn("Review limit reached", prior_error)
                    preserved = {path: path.read_bytes() for directory in
                                 (run.tasks, run.outputs, run.reviews, run.logs)
                                 for path in directory.rglob("*")
                                 if path.is_file() and path != summary_path}
                    turn_count = len(turns)
                    with patch.dict("workflow.os.environ", {
                        "HERDR_ENV": "1", "HERDR_WORKSPACE_ID": "w6", "HERDR_PANE_ID": "w6:p1",
                    }), patch("workflow.check_codex_login"):
                        with self.assertRaisesRegex(ValueError, "passed the review protocol"):
                            resume(run.run_id, reviewer_tool="codex")
                        self.assertEqual(resume(run.run_id, reviewer_tool="codex",
                                                authorize_round_four=True), int(not approve))
                        if not approve:
                            with self.assertRaisesRegex(ValueError, "passed the review protocol"):
                                resume(run.run_id, reviewer_tool="codex", authorize_round_four=True)
                    expected_turns = ["logistics-r4", "marketing-r4", "reviewer-r4"]
                    if approve:
                        expected_turns.append("coordinator-r1")
                    self.assertEqual([turn for turn, _ in turns[turn_count:]], expected_turns)
                    self.assertEqual(review_tools[-1], "codex")
                    self.assertEqual(read_json(run.logs / "review-checkpoint-r4.json")["round"], 4)
                    self.assertFalse((run.outputs / "budget-r4").exists())
                    summary = read_json(summary_path)
                    self.assertEqual(summary["round_four_authorization"]["previous_error"], prior_error)
                    self.assertEqual(summary["round_four_authorization"]["findings"],
                                     {"L1": "logistics", "M1": "marketing"})
                    if approve:
                        self.assertEqual(summary["review_rounds"], 4)
                        self.assertIn("outputs/demo-02/budget-r3/budget.md",
                                      read_json(run.tasks / "coordinator-r1.json")["dependencies"])
                    else:
                        self.assertEqual(summary["status"], "unresolved")
                        self.assertIn("Review limit reached with open findings", summary["error"])
                    for path, content in preserved.items():
                        self.assertEqual(path.read_bytes(), content)
                    return
                if reject_final_report:
                    run.tasks.mkdir()
                    summary_path = run.logs / "run.json"
                    summary_data = {"run": "fixture", "opencode_model": run.model, "panes": panes}
                    self.assertEqual(record_run(run, summary_data, run.execute), 1)
                    self.assertIn("'closed' is not outstanding", read_json(summary_path)["error"])
                    report_path = run.reviews / "reviewer-r3/review.json"
                    rejected = report_path.read_bytes()
                    preserved = {path: path.read_bytes() for path in [
                        *run.outputs.glob("*/*"), *run.reviews.glob("validation-*.json"),
                        *run.reviews.glob("reviewer-r[12]/review.json"),
                        *(p for p in run.tasks.glob("*.json") if p.stem != "reviewer-r3"),
                    ]}
                    turn_count = len(turns)
                    with patch.dict("workflow.os.environ", {
                        "HERDR_ENV": "1", "HERDR_WORKSPACE_ID": "w6", "HERDR_PANE_ID": "w6:p1",
                    }), patch("workflow.check_codex_login"):
                        self.assertEqual(resume("fixture", reviewer_tool="codex"), int(not approve))
                        if not approve:
                            with self.assertRaisesRegex(ValueError, "passed the review protocol"):
                                resume("fixture", reviewer_tool="codex")
                    expected_turns = [("reviewer-r3", run.model)]
                    if approve:
                        expected_turns.append(("coordinator-r1", run.model))
                    self.assertEqual(turns[turn_count:], expected_turns)
                    self.assertEqual(review_tools[-1], "codex")
                    self.assertEqual((run.logs / "reviewer-r3.rejected-review.json").read_bytes(),
                                     rejected)
                    summary = read_json(summary_path)
                    if approve:
                        self.assertEqual(summary["status"], "approved")
                        self.assertTrue((root / summary["package"]).is_file())
                    else:
                        self.assertEqual(summary["status"], "unresolved")
                        self.assertIn("Review limit reached with open findings", summary["error"])
                    self.assertEqual(summary["resumes"][-1]["previous_failure_kind"],
                                     "review_protocol")
                    for path, content in preserved.items():
                        self.assertEqual(path.read_bytes(), content)
                    return
                if retry_reviews:
                    run.tasks.mkdir()
                    summary_path = run.logs / "run.json"
                    summary_data = {"run": "fixture", "opencode_model": run.model, "panes": panes}
                    self.assertEqual(record_run(run, summary_data, run.execute), 1)
                    (run.logs / "review-checkpoint.json").unlink()
                    preserved = {path: path.read_bytes() for path in [
                        *run.outputs.glob("*/*"), *run.tasks.glob("*-r1.json"),
                        run.reviews / "validation-r1.json", run.logs / "reviewer-r1.log",
                    ] if path.name != "reviewer-r1.json"}
                    with patch.dict("workflow.os.environ", {
                        "HERDR_ENV": "1", "HERDR_WORKSPACE_ID": "w6", "HERDR_PANE_ID": "w6:p1",
                    }), patch("workflow.check_free_model") as verify, patch("workflow.check_codex_login"):
                        with patch.dict("workflow.os.environ", {
                            "HERDR_WORKSPACE_ID": "w7", "HERDR_PANE_ID": "w7:p1",
                        }):
                            with self.assertRaisesRegex(ValueError, "one Herdr workspace"):
                                resume("fixture", "opencode/alternate-free")
                        if reviewer_tool == "codex":
                            with self.assertRaisesRegex(ValueError, "--model selects"):
                                resume("fixture", "opencode/alternate-free", reviewer_tool)
                            self.assertEqual(resume("fixture", reviewer_tool=reviewer_tool), 1)
                        else:
                            self.assertEqual(resume("fixture", "opencode/alternate-free"), 1)
                        self.assertEqual(resume("fixture", None), 0)
                    self.assertEqual(verify.call_count, 0 if reviewer_tool == "codex" else 2)
                    summary = read_json(summary_path)
                    self.assertEqual(turns[0][0], "logistics-r1")
                    self.assertCountEqual([turn for turn, _ in turns[1:3]],
                                          ["budget-r1", "marketing-r1"])
                    self.assertEqual([turn for turn, _ in turns[3:]], [
                        "reviewer-r1", "reviewer-r1",
                        "marketing-r2", "reviewer-r2", "reviewer-r2", "coordinator-r1",
                    ])
                    self.assertEqual(review_tools, ["opencode", *[reviewer_tool] * 3])
                    expected_model = run.model if reviewer_tool == "codex" else "opencode/alternate-free"
                    self.assertEqual(turns[-3][1], expected_model)
                    self.assertEqual(summary["opencode_model"], expected_model)
                    self.assertEqual(summary["reviewer_tool"], reviewer_tool)
                    self.assertEqual(summary["resumes"][0]["previous_reviewer_tool"], "opencode")
                    self.assertEqual(summary["resumes"][0]["reviewer_tool"], reviewer_tool)
                    self.assertEqual(summary["resumes"][0]["previous_model"], run.model)
                    self.assertEqual(summary["resumes"][0]["previous_failure_kind"], "rate_limit")
                    self.assertEqual(summary["resumes"][1]["attempt"], "reviewer-r2-retry2")
                    for path, content in preserved.items():
                        self.assertEqual(path.read_bytes(), content)
                elif approve:
                    summary = run.execute()
                else:
                    with self.assertRaisesRegex(RuntimeError, "Review limit reached.*M1"):
                        run.execute()
                    self.assertEqual(run.revisions["reviewer"], 3)
                    self.assertEqual(run.revisions["marketing"], 3)
                    self.assertEqual(run.revisions["coordinator"], 0)
                    return

            self.assertEqual(summary["status"], "approved")
            self.assertEqual(summary["review_rounds"], 2)
            self.assertTrue((root / summary["package"]).is_file())
            for revision in (1, 2):
                self.assertTrue((run.outputs / f"marketing-r{revision}/marketing.md").is_file())
                self.assertTrue((run.reviews / f"reviewer-r{revision}/review.json").is_file())


if __name__ == "__main__":
    unittest.main()
