#!/usr/bin/env bash
set -euo pipefail

RUN_ID="${1:-}"
ROUND="${2:-}"
DAY="${3:-}"

if [[ -z "$RUN_ID" || -z "$ROUND" || -z "$DAY" ]]; then
  echo "[CHK] USAGE: check_checkpoint_chain.sh <Run_ID> <round> <YYYY-MM-DD>"
  exit 2
fi

FILE="Audit-Report/${DAY}/receipts/exec_checkpoint_${RUN_ID}_round${ROUND}.jsonl"

if [[ ! -f "$FILE" ]]; then
  echo "[CHK] MISSING_FILE: $FILE"
  exit 10
fi
if [[ ! -s "$FILE" ]]; then
  echo "[CHK] EMPTY_FILE: $FILE"
  exit 11
fi

python3 - "$FILE" <<'PY'
import json,sys
from collections import defaultdict

path = sys.argv[1]
required = ["T1","T2","T3","T4"]
seen = defaultdict(list)

with open(path, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        line=line.strip()
        if not line:
            continue
        try:
            obj=json.loads(line)
        except Exception:
            print(f"[CHK] INVALID_JSON_LINE:{i}")
            sys.exit(20)
        task=obj.get("task")
        if task:
            seen[task].append(obj)

for t in required:
    if t not in seen:
        print(f"[CHK] MISSING_{t}")
        sys.exit(30)

# take last record per task by seq if present else last
for t in required:
    rows=seen[t]
    rows=sorted(rows, key=lambda x: x.get('seq', 0))
    row=rows[-1]
    if row.get('wait_sent_via_toolcall') is not True:
        print(f"[CHK] WAIT_NOT_TOOLCALL:{t}")
        sys.exit(40)
    if row.get('ack_status') != 'MATCH':
        print(f"[CHK] ACK_NOT_MATCH:{t}:{row.get('ack_status')}")
        sys.exit(41)

print("[CHK] PASS")
PY
