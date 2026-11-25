# WSL setup and verification

Run the commands from the repository root in Ubuntu under WSL.

```bash
bash scripts/setup_workspace.sh --check
python3 -m unittest discover -s tests -v
python3 scripts/status.py
```

Development verified Herdr 0.9.5, Codex CLI 0.172.0 (ChatGPT login), OpenCode
2.4.1, Python 3.12.3, Git 2.43.0, and jq 1.7. OpenCode needed writable XDG
directories to print help and its version inside the development sandbox.
If you see an OpenCode write error in normal WSL, check that your user can
write to its XDG data, state, and cache directories.

The integration uses one workspace, five tabs with one terminal each, and
`herdr pane run` with the returned pane IDs. The coordinator's terminal runs
the driver and its Codex turns. Each other terminal runs its own CLI and role
instructions. Herdr submits the job while task files report actual completion.
Independent budget and marketing turns can overlap.

For the later live phase, use `opencode models` and confirm through OpenCode
that your chosen `opencode/<model>-free` model is currently free. The launch
script requires that model ID explicitly. Keep Codex logged in with ChatGPT.
No paid API billing is needed. Inside a Herdr-managed terminal:

```bash
bash scripts/setup_workspace.sh --launch demo-01 opencode/REPLACE-with-confirmed-model-free
python3 scripts/status.py demo-01
```

The checked-in CEO brief is `inputs/client_request.md`. Put any CEO changes
there before the run and freeze it for both experiments. Check progress with
the status script or the coordinator tab. If a turn fails, inspect the
corresponding task, pane, and log.

To resume demo-02 after repeated OpenCode HTTP 429 errors, run the following
from the Coordinator tab of the original Herdr workspace. Keep the original
worker tabs open and Codex logged in through ChatGPT.

```bash
python3 scripts/workflow.py resume demo-02 --reviewer-tool codex
```

Resume retries the saved assignment in the original Reviewer tab as a
separate Codex invocation. Later review rounds use the same tool. The driver
continues to automate revision assignments, machine validation, independent
verification, and final assembly after approval. Completed drafts and earlier
attempt logs are preserved. The run summary records the reviewer tool and the
failure that preceded the retry.

Marketing completed its first draft with OpenCode, so demo-02 has already used
both CLI tools successfully. Any marketing revisions still use OpenCode with
the saved free model. The planned switch is recorded in
[`logs/demo-02/reviewer-tool-change.md`](../logs/demo-02/reviewer-tool-change.md).

For other retries, omit both flags to reuse the saved reviewer tool (OpenCode
for older runs). Use `--reviewer-tool opencode` to select OpenCode with the
saved model, or `--model opencode/<model>-free` to select OpenCode with a
different model. OpenCode reviewer retries check the model against
`opencode models`.

The same resume command retries a completed reviewer turn whose report failed
the review protocol. It reuses the saved round, specialist artifacts, and
validation. The rejected JSON is archived under `logs/<run-id>/` with the
`.rejected-review.json` suffix.

From the original Coordinator tab, use the explicitly authorized final round
for demo-02 after its accepted round-three report left findings open:

```bash
python3 scripts/workflow.py resume demo-02 --reviewer-tool codex --authorize-round-four
```

The coordinator assigns targeted Logistics and Marketing revisions and reuses
Budget r3. Round four validates the current files and runs an independent
review in the original Reviewer tab. The coordinator assembles the package
only after approval. An open finding at the end of round four leaves demo-02
unresolved. Other runs retain the three-round limit.

Use the baseline command separately during the experiment phase:

```bash
python3 scripts/workflow.py baseline baseline-01
```

The baseline uses a separate Git root, input copies, one Codex invocation,
its own deliverables and logs, and the same numeric validator.

Herdr references consulted during development.

- [Herdr repository](https://github.com/herdrdev/herdr)
- [Herdr documentation](https://herdr.dev/tui/docs/)
- [Agent automation](https://herdr.dev/tui/docs/agent-automation/)
- [CLI reference](https://herdr.dev/tui/docs/cli-reference/)
