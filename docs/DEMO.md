# Demo video script

Target length is about 1 minute 45 seconds. Run the commands from the
repository root using the saved evidence. If the original Herdr workspace
is open, show the five tab labels beside the pane map. Use the commands
below for the rest of the video.

## 0:00–0:20 · Brief, roles, and tools

> Eventify planned a 50-student Women in Tech event on a $300 cap. Five
> agents worked in one Herdr workspace. Codex handled coordination,
> logistics, and budget. OpenCode wrote marketing. The independent reviewer
> switched to Codex after repeated rate limits.

```bash
jq '{run, panes, reviewer_tool}' logs/demo-02/run.public.json
jq -c '{role, tool: .command[0], ok}' logs/demo-02/{coordinator-r1,logistics-r4,budget-r3,marketing-r4,reviewer-r4}.result.json
```

## 0:20–0:40 · Automatic handoff

> The coordinator wrote task files that named the inputs and expected
> outputs. For the last revision, the marketing agent received the new
> logistics plan and the round-three review automatically.

```bash
jq '{role, status, dependencies: [.dependencies[] | select(contains("logistics-r4") or contains("reviewer-r3"))], expected_outputs}' tasks/demo-02/marketing-r4.json
```

## 0:40–1:10 · Finding, correction, and approval

> Round three caught an accessibility promise before the venue route had
> been checked. Marketing updated the caption, flyer, and email to say
> step-free access was planned and tell attendees where to get verified
> details. An authorized fourth round verified this and two logistics
> fixes. Validation passed, the reviewer approved, and the coordinator
> assembled the package.

```bash
jq -r '.findings[] | select(.id == "marketing-step-free-route-unverified") | .request' reviews/demo-02/reviewer-r3/review.json
rg -n -o 'is step-free|is planned and pending verification before doors open' outputs/demo-02/marketing-r{3,4}/marketing.md
cat reviews/demo-02/validation-r4.json
jq '{round, verdict, findings, verified: [.verified[].id]}' reviews/demo-02/reviewer-r4/review.json
python3 scripts/status.py demo-02
```

## 1:10–1:45 · Comparison and takeaway

> Both runs earned full marks on the rubric. The single-Codex baseline took
> about two minutes and budgeted $156. Demo-02 took 46 minutes elapsed,
> including interruptions, with about 27 minutes of active CLI time. It
> budgeted $300 and produced clearer volunteer backups through independent
> review. This was one run per approach, with different model setups and
> review opportunities.

```bash
sed -n '/^## Demo video scorecard$/,/^The six core files/{ /^The six core files/d; p; }' baseline/comparison.md
jq '{status, seconds, validation}' baseline/runs/baseline-01/result.json
```

[Full experiment evidence](EXPERIMENT.md) · [Scored comparison](../baseline/comparison.md#demo-video-scorecard) · [Approved package](../outputs/demo-02/coordinator-r1/event_package.md)
