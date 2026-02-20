#!/usr/bin/env bash
set -euo pipefail

# Operator closure gate for OpenModel-Eval-Self
# Usage:
#   scripts/operator_closure_gate.sh <Run_ID> [YYYY-MM-DD]
# Example:
#   scripts/operator_closure_gate.sh 20260219_1802 2026-02-19

RUN_ID="${1:-}"
DATE_DIR="${2:-$(date -u +%Y-%m-%d)}"

if [[ -z "$RUN_ID" ]]; then
  echo "[FATAL] missing Run_ID"
  echo "Usage: $0 <Run_ID> [YYYY-MM-DD]"
  exit 2
fi

BASE="Audit-Report/${DATE_DIR}"
R1="${BASE}/review_${RUN_ID}_round1.md"
R2="${BASE}/review_${RUN_ID}_round2.md"
RAW_DIR="${BASE}/raw_logs"

FAIL=0

ok() { echo "[OK] $*"; }
warn() { echo "[WARN] $*"; }
fail() { echo "[FAIL] $*"; FAIL=1; }

echo "[INFO] Run_ID=${RUN_ID} Date=${DATE_DIR}"

echo "[CHECK] review files exist"
[[ -f "$R1" ]] && ok "found $R1" || fail "missing $R1"
[[ -f "$R2" ]] && ok "found $R2" || fail "missing $R2"

echo "[CHECK] operator block placeholders cleaned"
PATTERN='(<PASS/FAIL>|<PASS/FAIL/INCOMPLETE>|OPERATOR_OVERRIDE_BLOCK_START|<正常 / 存在疏漏 / 执行失控>|<VALID / INVALID>)'
if grep -nE "$PATTERN" "$R1" "$R2" >/tmp/operator_gate_placeholders_${RUN_ID}.log 2>/dev/null; then
  fail "placeholder residue detected in review files"
  sed -n '1,30p' /tmp/operator_gate_placeholders_${RUN_ID}.log
else
  ok "no placeholder residue in review files"
fi

echo "[CHECK] round2 delta analysis present"
if grep -nE 'Delta Analysis|Native-Good|Prompt-Steerable|Hopeless|UNDECIDED|INVALID_COMPARISON' "$R2" >/dev/null 2>&1; then
  ok "Delta Analysis markers found in round2"
else
  fail "Delta Analysis markers missing in round2"
fi

echo "[CHECK] raw logs existence and non-empty"
if [[ -d "$RAW_DIR" ]]; then
  ok "found $RAW_DIR"
  COUNT=$(find "$RAW_DIR" -maxdepth 1 -type f -name "raw_${RUN_ID}_round*.jsonl" | wc -l | tr -d ' ')
  if [[ "$COUNT" -ge 2 ]]; then
    ok "raw logs count: $COUNT"
  else
    fail "raw logs count too low: $COUNT (expected >=2)"
  fi

  EMPTY=$(find "$RAW_DIR" -maxdepth 1 -type f -name "raw_${RUN_ID}_round*.jsonl" -size 0c | wc -l | tr -d ' ')
  if [[ "$EMPTY" -eq 0 ]]; then
    ok "all matched raw logs are non-empty"
  else
    fail "found $EMPTY empty raw logs"
  fi
else
  fail "missing $RAW_DIR"
fi

echo "[CHECK] opinion files present (operator/subagentA/subagentB)"
for f in \
  "${BASE}/opinion_${RUN_ID}_operator.md" \
  "${BASE}/opinion_${RUN_ID}_subagentA.md" \
  "${BASE}/opinion_${RUN_ID}_subagentB.md"; do
  [[ -f "$f" ]] && ok "found $(basename "$f")" || warn "missing $(basename "$f")"
done

if [[ "$FAIL" -ne 0 ]]; then
  echo "[GATE] BLOCKED: closure gate failed"
  exit 1
fi

echo "[GATE] PASS: safe to close/push"
