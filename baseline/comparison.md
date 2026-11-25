# Eventify experiment comparison

**Both runs scored 12/12 (100/100).** The single Codex run was faster and left more budget headroom. Demo-02 produced more detailed volunteer backups and a record of what independent review changed. The rubric awards one point per check, so both can earn full credit even when their plans differ in depth. The checked-in rubric has three categories worth four points each. The 100-point totals are the raw scores divided by 12 and multiplied by 100. [Evaluation rubric](evaluation_rubric.md)

## Demo video scorecard

| Measure | Demo-02 · Multi-agent | Baseline-01 · Single agent |
| --- | --- | --- |
| Quality score | **100/100 (12/12)** | **100/100 (12/12)** |
| Elapsed / active CLI time | **46m 16s / 27m 22s** | **2m 04.57s / 2m 04.57s** at recorded precision |
| Agents / AI tools | 5 roles / 2 tools (Codex and OpenCode) | 1 agent / 1 tool (Codex) |
| Schedule and staffing | 6 blocks, 16:00–19:00, 6 volunteers | Same block boundaries and volunteer count |
| Budget | $136 purchases + $164 reserve = **$300** | $126 purchases + $30 reserve = **$156** |
| Coverage | 60 food servings, 72 drinks, 75 tags | Same coverage |
| Core files | 6 of 6 | 6 of 6 |
| Checks | Validator passed, four independent review rounds, approved | Validator passed, one turn with self-review |

The six core files are Logistics and Budget in JSON and Markdown, Marketing Markdown with all three pieces, and the final Markdown package. The budget figures are planned allocations. Demo-02's elapsed time includes pauses and retries. Its active CLI time counts overlapping calls once. The baseline's run and sole CLI result each recorded 124.57 seconds, with no retry recorded. [Demo-02 metrics](../docs/EXPERIMENT.md#recorded-timing) · [Baseline result](runs/baseline-01/result.json) · [Baseline CLI result](runs/baseline-01/logs/single.result.json)

## How the points were earned

The same rubric was applied to both final packages and their source files.

| Rubric category | Demo-02 | Baseline-01 |
| --- | --- | --- |
| **Accuracy** | **4/4.** Six continuous blocks in the required order (+1), valid V1–V6 IDs (+1), correct catalog prices, totals and reserve (+1), sufficient food, drinks and tags for 50 (+1). [Agenda](../outputs/demo-02/logistics-r4/logistics.json) · [Budget](../outputs/demo-02/budget-r3/budget.json) · [Validator result](../reviews/demo-02/validation-r4.json) | **4/4.** Same six blocks (+1), valid V1–V6 IDs (+1), correct catalog arithmetic and $30 minimum reserve (+1), same food, drink and tag coverage (+1). [Agenda](runs/baseline-01/deliverables/logistics.json) · [Budget](runs/baseline-01/deliverables/budget.json) · [Validator result](runs/baseline-01/result.json) |
| **Completeness** | **4/4.** Staffing table and supply list (+1), access plan and contingencies (+1), itemized budget with replenishment procedure (+1), Instagram, flyer and email (+1). [Logistics](../outputs/demo-02/logistics-r4/logistics.md) · [Budget](../outputs/demo-02/budget-r3/budget.md) · [Marketing](../outputs/demo-02/marketing-r4/marketing.md) | **4/4.** Duties by block and supply checklist (+1), access plan and contingencies (+1), itemized budget and reserve notes (+1), Instagram, flyer and email (+1). [Logistics](runs/baseline-01/deliverables/logistics.md) · [Budget](runs/baseline-01/deliverables/budget.md) · [Marketing](runs/baseline-01/deliverables/marketing.md) |
| **Quality** | **4/4.** Explicit 16:22 desk handoff (+1), timed and owned speaker and volunteer fallbacks (+1), approved schedule, quantities and attendee claims agree across files (+1), copy uses a caption, scannable flyer and email subject/body (+1). [Final package](../outputs/demo-02/coordinator-r1/event_package.md) · [Independent review](../reviews/demo-02/reviewer-r4/review.json) | **4/4.** Volunteer duties are usable by block (+1), named owners handle concrete triggers such as 50 people admitted and projector or Wi-Fi failure (+1), schedule, supplies and promotional claims agree (+1), concise copy fits all three channels (+1). [Final package](runs/baseline-01/deliverables/event_package.md) · [Contingencies](runs/baseline-01/deliverables/logistics.md#contingencies) |
| **Total** | **12/12 → 100/100** | **12/12 → 100/100** |

## What each approach did better

- **Demo-02 made tricky handoffs easier to run.** The baseline tells V1 to assign backup coverage before doors open. Demo-02 also specifies what to do if V2 leaves during welcome, who takes the desk in person, and who posts written updates while V4 stays on accessibility. Independent review also caught a stale budget link and a step-free claim that Marketing r3 made before verification. The final review checked the replacements against the prior drafts. The detailed plan takes longer to scan, and Budget r3 still contains an older review note and links back to Logistics r3. The final reviewer checked that the linked procedures agree with the corresponding r4 sections. [Baseline contingencies](runs/baseline-01/deliverables/logistics.md#contingencies) · [Revised desk coverage](../outputs/demo-02/logistics-r4/logistics.md#if-v2-is-absent) · [Budget r3](../outputs/demo-02/budget-r3/budget.md) · [Final review](../reviews/demo-02/reviewer-r4/review.json)
- **Baseline-01 was leaner and handled some everyday problems explicitly.** It lists a walk-in cutoff at 50 admissions and tells V1 how to shorten the program if it runs late. Its Instagram caption is shorter, and it avoided promising an unverified step-free route in its first draft. The budget leaves $144 of headroom after its $30 reserve, with fewer markers and exactly 50 handouts. Demo-02 buys four extra markers and 25 extra copies for signs or backups and sets aside a larger reserve. Both cover the same food, drinks and tags. [Baseline logistics](runs/baseline-01/deliverables/logistics.md) · [Baseline marketing](runs/baseline-01/deliverables/marketing.md) · [Baseline budget](runs/baseline-01/deliverables/budget.md) · [Demo-02 budget](../outputs/demo-02/budget-r3/budget.md)

## Cost in time and limits of the comparison

Demo-02 used 33 CLI calls, including coordinator assignments and eight reviewer attempts. The reviewer attempts alone accounted for **7m 20.12s** of recorded CLI time. Three OpenCode attempts hit HTTP 429, which paused the run and led to a switch to Codex in the original Reviewer pane. A round-three report also needed a retry after listing already-closed findings. Those interruptions and the time spent coordinating revisions help explain the gap from the one-call baseline. [Timing and recovery evidence](../docs/EXPERIMENT.md#recorded-timing) · [Demo-02 run log](../logs/demo-02/run.public.json) · [Baseline CLI log result](runs/baseline-01/logs/single.result.json)

This is one trial per approach, run on November 24–25, 2026 UTC, with byte-identical copies of the brief, catalog and formats. Demo-02 Marketing used OpenCode's DeepSeek V4.1 Flash Free for its first draft and MiMo V2.6 Flash Free for later turns. Both experiments used Codex, but the saved Codex invocations do not identify the selected model, so an exact model match cannot be verified. Demo-02 had four review rounds and separate revision turns. The baseline had one turn with self-review. These differences prevent isolating the effect of agent count. The rubric measures document quality and compliance, with no live event test of either plan. [Marketing r1 invocation](../logs/demo-02/marketing-r1.result.json) · [Marketing r4 invocation](../logs/demo-02/marketing-r4.result.json) · [Baseline prompt](prompt.md)
