# Eventify

Eventify is a CS4680 Prompt Engineering project for planning student
organization events. Its fictional client event is **Women in Tech:
Connect & Grow**, a 50-student event with a $300 spending cap.

**Demo-02 finished approved after four review rounds.** Five agents worked
in one Herdr workspace. Codex ran the Coordinator, Logistics, and Budget
roles. OpenCode completed all Marketing turns. The independent Reviewer
switched from OpenCode to Codex in the original Reviewer tab after repeated
rate limits.

The Coordinator assigned tasks from the CEO brief, routed revisions from
review findings, and assembled the package after Python validation passed
and the Reviewer approved. The final run used Logistics r4, Budget r3, and
Marketing r4. The standard limit is three rounds. Demo-02 received explicit
authorization for one additional round.

[Experiment evidence and demo commands](docs/EXPERIMENT.md) · [Approved event package](outputs/demo-02/coordinator-r1/event_package.md)

**Baseline-01 also completed and passed validation.** One Codex agent
produced all six files in 2m 04.57s and budgeted $156 including reserve.
Demo-02 budgeted $300 and finished in 46m 16s elapsed, with 27m 22s of
active CLI time. Both scored 12/12 (100/100) on the rubric. Demo-02 added
more detailed fallback procedures through independent review.
[Side-by-side comparison](baseline/comparison.md)

## Verify locally

```bash
bash scripts/setup_workspace.sh --check
python3 -m unittest discover -s tests -v
python3 scripts/status.py demo-02
```

## Project files

- `agents/` and `inputs/` hold the role prompts, client brief, catalog, and formats.
- `scripts/` and `tests/` hold the Herdr dispatch, validation, and local tests.
- `tasks/`, `outputs/`, `reviews/`, and `logs/` store versioned run evidence.
- `baseline/` holds the single-Codex prompt, results, rubric, and comparison.

The submission evidence includes task files, deliverables, reviews, and
selected structured execution records. The public run summary uses
repository-relative paths. Local runner state and raw CLI transcripts are
ignored by Git. [Public demo-02 run summary](logs/demo-02/run.public.json)

See [setup](docs/SETUP.md), [demo plan](docs/DEMO.md), and the [course evidence
map](docs/RUBRIC.md). The video and GitHub submission are pending.
