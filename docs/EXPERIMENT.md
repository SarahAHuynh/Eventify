# Demo-02 experiment evidence

Eventify planned **Women in Tech: Connect & Grow**, an event for 50 college students with a $300 cap. Demo-02 finished **approved in round 4**, with all 16 task files marked completed. [Run record](../logs/demo-02/run.public.json) · [Final event package](../outputs/demo-02/coordinator-r1/event_package.md)

Baseline-01 completed in **2m 04.57s** with one Codex agent, all six core files, and zero validation errors. Both runs scored **12/12 (100/100)**. The baseline planned $156 including reserve, while demo-02 planned $300 and documented more detailed fallback procedures. [Baseline result](../baseline/runs/baseline-01/result.json) · [Demo video scorecard](../baseline/comparison.md#demo-video-scorecard)

## Five roles in one Herdr workspace

The launcher created the Coordinator tab in the workspace root, then opened four worker tabs in the same workspace. The saved pane IDs all start with `w6:`. The run record stores the four worker IDs. The launcher shows how it uses the workspace's root pane for the Coordinator. Budget and Marketing overlapped in round 1, with recorded starts less than a millisecond apart. [Herdr launcher](../scripts/setup_workspace.sh) · [Saved pane map](../logs/demo-02/run.public.json)

| Role | Terminal | Tool and evidence |
| --- | --- | --- |
| Coordinator | Workspace root | Codex assigned tasks and assembled the package. [Assignment result](../logs/demo-02/assign-budget-r1-marketing-r1.result.json) · [Assembly result](../logs/demo-02/coordinator-r1.result.json) |
| Logistics | `w6:p2` | Codex wrote the agenda, staffing, and contingencies. [Logistics r4 result](../logs/demo-02/logistics-r4.result.json) |
| Budget | `w6:p3` | Codex priced catalog packs and planned the reserve. [Budget r1 result](../logs/demo-02/budget-r1.result.json) |
| Marketing | `w6:p4` | OpenCode completed all four marketing turns. [Marketing r1 result](../logs/demo-02/marketing-r1.result.json) · [Marketing r4 result](../logs/demo-02/marketing-r4.result.json) |
| Independent Reviewer | `w6:p5` | OpenCode attempted the first review. Separate Codex invocations in the same pane produced the accepted reviews. [OpenCode retry result](../logs/demo-02/reviewer-r1-retry2.result.json) · [Codex review result](../logs/demo-02/reviewer-r1-retry3.result.json) |

## Automated assignments and handoffs

- The Coordinator turned the brief into a Logistics task. Once Logistics finished, the runner handed its JSON and Markdown to Budget and Marketing and dispatched both tasks. The task files record dependencies, expected output paths, and completion. [Brief](../inputs/client_request.md) · [Logistics task](../tasks/demo-02/logistics-r1.json) · [Budget task](../tasks/demo-02/budget-r1.json) · [Marketing task](../tasks/demo-02/marketing-r1.json)
- The fourth-round Logistics task received the round-three review, validation, and exact Budget r3 files. Marketing r4 then received Logistics r4 and the same review. The Reviewer received both revised filesets, the retained Budget r3, and the new validation. The Coordinator's assembly task names the approved inputs. [Logistics r4 task](../tasks/demo-02/logistics-r4.json) · [Marketing r4 task](../tasks/demo-02/marketing-r4.json) · [Reviewer r4 task](../tasks/demo-02/reviewer-r4.json) · [Assembly task](../tasks/demo-02/coordinator-r1.json)

## Four review rounds

| Round | Verdict | What happened |
| --- | --- | --- |
| 1 | Revise | Found gaps in who covers V5's refreshment prep and shortages and who covers V1's check-in, welcome, icebreaker, and closing duties. [Review](../reviews/demo-02/reviewer-r1/review.json) |
| 2 | Revise | Verified both round-one fixes. Found a gap when V1 and V5 absences overlap during welcome and a Logistics handoff still pointing to Budget r1. [Review](../reviews/demo-02/reviewer-r2/review.json) |
| 3 | Revise | The accepted retry verified the overlapping-absence fix. Three issues remained. Logistics linked to Budget r2, V2's desk and written-update duties lacked a backup, and Marketing presented the step-free route as confirmed. [Accepted review](../reviews/demo-02/reviewer-r3/review.json) |
| 4 | Approve | Verified all three outstanding fixes, rechecked earlier fixes, and reported zero open findings. Budget r3 carried forward. [Review](../reviews/demo-02/reviewer-r4/review.json) |

## Before and after

| Reviewer feedback | Before | After |
| --- | --- | --- |
| Round 1 asked who would count, stage, and label refreshments if V5 missed setup. | “move V2 to the food station during the break” [Logistics r1](../outputs/demo-02/logistics-r1/logistics.md#contingencies) | “V2 counts usable food and drinks, stages first servings and surplus separately, and starts the shortage response if needed.” Budget also gives V2 the backup labeling duties. [Logistics r2](../outputs/demo-02/logistics-r2/logistics.md#if-v5-is-absent) · [Budget r2](../outputs/demo-02/budget-r2/budget.md#refreshment-shortage-procedure) |
| Round 2 asked for an explicit desk handoff when V5 leaves during welcome while V1 is already absent. | “V2 takes the first pause in the current block to verify the tally” [Logistics r2](../outputs/demo-02/logistics-r2/logistics.md#if-v5-is-absent) | “V6 says ‘I have check-in’ to V2 in person before V2 leaves” (quotation marks normalized). The revised plan also covers the speaker briefing if V6 is still on the desk. [Logistics r3](../outputs/demo-02/logistics-r3/logistics.md#opening-desk-handoff-when-v5-is-absent) |
| Round 3 asked Logistics to link to the current shortage procedure. | `../budget-r2/budget.md#refreshment-shortage-procedure` [Logistics r3](../outputs/demo-02/logistics-r3/logistics.md#opening-desk-handoff-when-v5-is-absent) | `../budget-r3/budget.md#refreshment-shortage-procedure` [Logistics r4](../outputs/demo-02/logistics-r4/logistics.md#if-v2-is-absent) · [Budget r3 target](../outputs/demo-02/budget-r3/budget.md#refreshment-shortage-procedure) |
| Round 3 asked who takes V2's desk and written updates while V4 stays on access. | “If V2 is absent, fold questions into the moderated discussion and use one refreshment station.” [Logistics r3](../outputs/demo-02/logistics-r3/logistics.md#contingencies) | “When V2 is absent, V6 owns written schedule updates.” V6 also takes the desk in person by 16:22 when V1 is present. [Logistics r4](../outputs/demo-02/logistics-r4/logistics.md#if-v2-is-absent) |
| Round 3 asked all three marketing pieces to qualify the step-free claim. | “The route from arrival to seating, refreshments, and the restroom is step-free” [Marketing r3](../outputs/demo-02/marketing-r3/marketing.md) | “is planned and pending verification before doors open” in Instagram, the flyer, and the email. Each tells attendees to check the RSVP link or check-in for verified details. [Marketing r4](../outputs/demo-02/marketing-r4/marketing.md) |

## Recovery and final checks

Three OpenCode reviewer attempts hit HTTP 429 across the free DeepSeek and MiMo models. The runner resumed the saved review in the original Reviewer pane using Codex. The first round-three report repeated two already-closed IDs in `verified`. Recovery archived that JSON and retried only the review against the same specialist files. After the accepted retry left three real issues open, explicit authorization allowed one final demo-02 round. The Coordinator assigned Logistics and Marketing fixes and kept Budget r3. The default remains three rounds. [Tool-switch record](../logs/demo-02/reviewer-tool-change.md) · [Rejected report](../logs/demo-02/reviewer-r3.rejected-review.json) · [Resume and authorization history](../logs/demo-02/run.public.json)

Machine validation passed in all four rounds. Round 4 returned `passed: true` and an empty error list. The reviewer verified all three outstanding findings and approved with an empty findings list. The final package uses Logistics r4, Budget r3, and Marketing r4. It covers 60 food servings, 72 drinks, and 75 name tags, with $136 in planned spending and a $164 reserve for a $300 total. [Final validation](../reviews/demo-02/validation-r4.json) · [Approval](../reviews/demo-02/reviewer-r4/review.json) · [Package](../outputs/demo-02/coordinator-r1/event_package.md)

## Recorded timing

| Measure | Value |
| --- | ---: |
| Elapsed from run start to final assembly task completion, including interruptions | **46m 16.34s** |
| Observed active CLI time with overlapping calls counted once | **27m 21.99s** |
| Total time across individual CLI calls, counting overlap in each call | **29m 02.78s** |
| Final continuation, from round-four authorization through approval and assembly | **7m 12.56s** |

Elapsed time uses the run start at 23:18:22.907430 UTC on November 24, 2026, and the assembly task finish at 00:04:39.245639 UTC on November 25. Active time merges the intervals from `started_utc` through `started_utc + seconds` in 33 CLI result files, including failed attempts. Time outside those intervals includes interruptions and workflow overhead. The logs show 26 Codex calls that exited successfully and seven OpenCode calls, four successful and three rate-limited. The rejected round-three report came from a successful CLI call that failed the workflow's separate review check. The final `run.json` duration covers the last continuation. [Run timing](../logs/demo-02/run.public.json) · [Assembly task timestamp](../tasks/demo-02/coordinator-r1.json) · [CLI result files](../logs/demo-02/)

## Demo video commands

Run these read-only commands from the repository root. Show the five labeled tabs in Herdr if the original workspace is still open.

```bash
# Completed tasks, panes, and successful turns from both tools
python3 scripts/status.py demo-02
jq '{panes, status, review_rounds}' logs/demo-02/run.public.json
jq '{role, tool: .command[0], ok}' logs/demo-02/{coordinator-r1,logistics-r4,budget-r3,marketing-r4,reviewer-r4}.result.json

# Automated handoff and the findings carried into round four
jq '{role, status, dependencies, expected_outputs}' tasks/demo-02/marketing-r4.json
jq '{round, verdict, findings: [.findings[] | {id, request}]}' reviews/demo-02/reviewer-r3/review.json

# Before and after for the step-free statement in all three marketing pieces
rg -n 'is step-free|pending verification' outputs/demo-02/marketing-r{3,4}/marketing.md

# Final validation, approval, and package evidence
cat reviews/demo-02/validation-r4.json
jq '{round, verdict, findings, verified: [.verified[].id]}' reviews/demo-02/reviewer-r4/review.json
sed -n '/^## Approval and evidence/,$p' outputs/demo-02/coordinator-r1/event_package.md
```
