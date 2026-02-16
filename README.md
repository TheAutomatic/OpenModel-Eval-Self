# OpenModel-Eval-Self

Runbooks and artifacts for evaluating OpenClaw integrated model reliability.

## Folders

### `Audit-Report/`
All self-audit outputs live here, organized by date:

- `Audit-Report/YYYY-MM-DD/exec_openclaw_run<run_id>_round<1|2>.md` — executor (subagent) evidence report
- `Audit-Report/YYYY-MM-DD/review_openclaw_run<run_id>_round<1|2>.md` — reviewer (main session) audit verdict
- `Audit-Report/YYYY-MM-DD/_sessions/` — gzipped OpenClaw session JSONL archives used as arbitration evidence

This repo is the **single source of truth** for audit artifacts; do not write new audit outputs into the global workspace `memory/`.

## Runbooks
- `WORKFLOW-OpenClaw-SelfAudit-REVIEW.md` — reviewer (main session) workflow (KR mode A)
- `WORKFLOW-OpenClaw-SelfAudit-EXEC.md` — executor (subagent) workflow (KR mode A)

## External Reviewer Guide
- `CLAUDE-REVIEW-GUIDE.md` — how Claude should read one run, validate evidence closure, and produce actionable feedback (`MUST FIX / SHOULD IMPROVE / NIT`).
