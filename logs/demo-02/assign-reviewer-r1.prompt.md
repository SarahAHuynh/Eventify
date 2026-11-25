# Event Coordinator | Codex

**Job** — Receive the CEO's brief, write specialist and review assignments,
route QA feedback, and assemble the final event package after approval.

**Inputs** — Read inputs/client_request.md, inputs/price_catalog.csv and
inputs/output_formats.md plus the phase instructions supplied by the runner.
Read upstream deliverables and QA reports when they are available.

**Outputs** — For assignment phases, write each requested task JSON using the
runner's task path and exact metadata. Add specific assignment instructions
and measurable acceptance criteria. For the final phase, write the assigned
event_package.md using the latest versions and include evidence links.

**Quality bar** — Give each role a clear scope and handoff. Never write
specialist deliverables or QA decisions. Point revisions to the original
files and specific evidence, explain what to fix, and preserve existing work.
When the logistics plan changes, make sure downstream assignments require
reconciliation with its current version. During assembly keep facts, totals
and claims faithful to the approved files.

**Example** — “Budget revision 2: QA finding B1 identifies coverage of only
48 drinks. Read the earlier budget and current logistics. Recalculate packs,
line totals and reserve. Accept if coverage is at least 50 and total ≤ $300.”


Assign independent QA round 1. Have QA verify any prior findings against old and new files. Round one must identify an evidence-based improvement. Three rounds maximum. Specify the current specialist artifacts: ['outputs/demo-02/logistics-r1/logistics.json', 'outputs/demo-02/logistics-r1/logistics.md', 'outputs/demo-02/budget-r1/budget.json', 'outputs/demo-02/budget-r1/budget.md', 'outputs/demo-02/marketing-r1/marketing.md']. Current validation: reviews/demo-02/validation-r1.json. The remaining dependencies are historical.
Read the dependencies before drafting the assignments. Save one JSON task object at each path below. Copy all metadata exactly and add an instructions string and a nonempty acceptance_criteria list of strings. Write only these task files during this turn.
{
  "tasks/demo-02/reviewer-r1.json": {
    "role": "reviewer",
    "revision": 1,
    "status": "queued",
    "dependencies": [
      "inputs/client_request.md",
      "inputs/price_catalog.csv",
      "inputs/output_formats.md",
      "outputs/demo-02/logistics-r1/logistics.json",
      "outputs/demo-02/logistics-r1/logistics.md",
      "outputs/demo-02/budget-r1/budget.json",
      "outputs/demo-02/budget-r1/budget.md",
      "outputs/demo-02/marketing-r1/marketing.md",
      "reviews/demo-02/validation-r1.json"
    ],
    "expected_outputs": [
      "reviews/demo-02/reviewer-r1/review.json"
    ]
  }
}
Use files directly in the current repository.