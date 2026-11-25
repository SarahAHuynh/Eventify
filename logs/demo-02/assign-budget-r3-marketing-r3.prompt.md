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


Route each role's applicable reviewer findings and require reconciliation with current logistics. If a role has no finding, assign a dependency refresh.
Read the dependencies before drafting the assignments. Save one JSON task object at each path below. Copy all metadata exactly and add an instructions string and a nonempty acceptance_criteria list of strings. Write only these task files during this turn.
{
  "tasks/demo-02/budget-r3.json": {
    "role": "budget",
    "revision": 3,
    "status": "queued",
    "dependencies": [
      "inputs/client_request.md",
      "inputs/price_catalog.csv",
      "inputs/output_formats.md",
      "outputs/demo-02/logistics-r3/logistics.json",
      "outputs/demo-02/logistics-r3/logistics.md",
      "outputs/demo-02/budget-r2/budget.json",
      "outputs/demo-02/budget-r2/budget.md",
      "reviews/demo-02/reviewer-r2/review.json",
      "reviews/demo-02/validation-r2.json"
    ],
    "expected_outputs": [
      "outputs/demo-02/budget-r3/budget.json",
      "outputs/demo-02/budget-r3/budget.md"
    ]
  },
  "tasks/demo-02/marketing-r3.json": {
    "role": "marketing",
    "revision": 3,
    "status": "queued",
    "dependencies": [
      "inputs/client_request.md",
      "inputs/price_catalog.csv",
      "inputs/output_formats.md",
      "outputs/demo-02/logistics-r3/logistics.json",
      "outputs/demo-02/logistics-r3/logistics.md",
      "outputs/demo-02/marketing-r2/marketing.md",
      "reviews/demo-02/reviewer-r2/review.json",
      "reviews/demo-02/validation-r2.json"
    ],
    "expected_outputs": [
      "outputs/demo-02/marketing-r3/marketing.md"
    ]
  }
}
Use files directly in the current repository.