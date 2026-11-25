# Compare the completed experiments

Freeze the shared inputs and model settings before running either experiment.
Record the CLI versions, Codex model, OpenCode model, date, run IDs, and any
interruptions. Evaluate the final packages with the same rubric and include
file and section evidence for each score. Use the same evaluator for both.

| Dimension | Points | Evidence |
| --- | ---: | --- |
| Accuracy | 0–4 | One point each for schedule, staffing IDs, catalog arithmetic and limits, and 50-person coverage passing the same validator. |
| Completeness | 0–4 | One point each for an actionable staffing/supply plan, accessibility and contingencies, a usable itemized budget, and all three promotional pieces. |
| Quality | 0–4 | One point each for executable volunteer duties, concrete fallback triggers and owners, cross-document consistency, and clear channel-appropriate copy. |

| Metric | Multi-agent | Single Codex | Evidence and limitations |
| --- | --- | --- | --- |
| Accuracy / 4 | Pending | Pending | |
| Completeness / 4 | Pending | Pending | |
| Quality / 4 | Pending | Pending | |
| End-to-end workflow seconds | Pending | Pending | |
| Unresolved checks and missing files | Pending | Pending | |
| Revision and review overhead | Pending | Pending | |

Use `logs/<run>/run.json` and `baseline/runs/<run>/result.json` for time.
The multi-agent timer includes assignments, dispatch, review and revisions.
Both timers exclude setup and begin before the first model call. Compare actual
files and failure states. Treat missing outputs as missing evidence. Report
multi-agent review overhead and any quality improvements with artifact links.
A single trial and different tools/models limit causal conclusions. Record
rate limits or blocking prompts and whether either run was interrupted.
