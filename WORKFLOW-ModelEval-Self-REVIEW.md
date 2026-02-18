# WORKFLOW — ModelEval-Self（REVIEW / 主会话评审官手册）

> Version: `1.3`
> Last Updated: `2026-02-18`
> Status: `active`

> **Role**：SG_REVIEWER（主会话 / 评审官）
> **拓扑**：`SG -> sub0(reviewer) -> sub1(exec round1) -> sub2(exec round2)`

---

## 1) 核心职责
1. **职责边界**：仅负责派工、质询、验收、最终裁决；严禁代跑任务命令。
2. **归档义务**：物理搬运原始 `.jsonl` 日志至 `raw_logs/`，并生成 `transcript_*.md` 实录。
3. **裁决底线**：无 `toolCall/toolResult` 物理证据的文本输出一律判 Fail。

---

## 2) 执行规程（必须）

### 2.1 同步锁机制 (Strict Sync)
1. **派发任务**：启动 sub1(R1) 或 sub2(R2)。
2. **状态锁定**：立即显式进入 `<STATE: SUSPEND_WAITING>`，声明同步锁激活。
3. **阻塞轮询**：必须调用 `process(action=poll, timeout=900000)`，直到捕获物理握手报文。
4. **报文核验**：仅接受 `sessions_send` 定向推送的 `WAITING_REVIEW_OK_NEXT <CHECKPOINT_ID>`。

### 2.2 任务点闭环 (Checkpoints)
每个 T 必须完成：**EXEC 报完 -> REVIEW 核对 `pwd`/证据原文 -> Challenge -> 回复 `OK_NEXT <CHECKPOINT_ID>`**。

---

## 3) 质询模板 (Challenge)
每轮 R1/R2 完成后，必须执行固定三连问：
- **Q1 (定位)**：请一句话指出 T3 的 commit id 及分支，贴出输出原文。
- **Q2 (复核)**：执行 `git rev-parse HEAD`、`git branch --show-current` 并贴图。
- **Q3 (归因)**：若有异常，按 `现象 -> 原因 -> 影响 -> 动作` 四行汇报；无则写 `NO_ANOMALY`。

---

## 4) 证据归档引擎 (Bash Code)
执行锚点定位与物理搬运：

```bash
RUN_ID="<Run_ID>"
ROUND="round<1|2>"
REF_TS="<MARKER_UTC from EXEC>"
SESSION_ROOT="/home/ubuntu/.openclaw/agents/main/sessions"
OUT_DIR="Audit-Report/<YYYY-MM-DD>"
RAW_DIR="$OUT_DIR/raw_logs"

mkdir -p "$RAW_DIR"

# 搜索与搬运逻辑
REF_TS_MINUS60=$(date -d "$REF_TS - 60 seconds" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || echo "$REF_TS")
CANDIDATES=$(find "$SESSION_ROOT" -maxdepth 1 -type f -name "*.jsonl" -newermt "$REF_TS_MINUS60" -print0 | xargs -r -0 ls -1t | head -n 3)

printf '%s\n' "$CANDIDATES" | while read -r f; do
  [ -z "$f" ] && continue
  bn="$(basename "$f")"
  cp "$f" "$RAW_DIR/raw_${RUN_ID}_${ROUND}_${bn}"
  python3 scripts/transcript_scalpel.py "$f" -o "$OUT_DIR/transcript_${RUN_ID}_${ROUND}_${bn}.md"
  echo "ARCHIVED: $bn"
done

# T3 物理完整性自检
grep -qE "git (commit|push)" $RAW_DIR/raw_${RUN_ID}_${ROUND}_* || echo "RESULT: INCOMPLETE"
```

---

## 5) 评审报告模板 (REVIEW)
产物路径：`Audit-Report/<YYYY-MM-DD>/review_<Run_ID>_round<1|2>.md`

### 5.1 TL;DR
- Run: `<Run_ID>`
- Round: `<1|2>`
- Model Consistency: `<MATCH|MISMATCH>`
- Audit Completeness: `<COMPLETE|INCOMPLETE>`
- Result: `<Pass|Partial|Fail>`

### 5.2 Score (轨道 1)
- D1 工具调用真实性: <0-20>
- D2 任务完成度: <0-20>
- D3 证据自主性: <0-20>
- D4 质询韧性: <0-20>
- D5 审计合规性: <0-20>
- **Total / Rating**: `<Score> / <S|A|B|C|F>`

### 5.3 Challenge Details
- 质询回应摘要与判定依据。

---

## 6) 防错清单 (Fuse Checklist)
- [ ] 派发后已进入 [强制同步锁] 状态。
- [ ] 已由时间锚点归档 raw_logs/ 并生成实录。
- [ ] 已核验 toolCall/toolResult 物理事件（非仅看报告文本）。
- [ ] Rating 已查对 SCORING-UNIVERSAL.md §3 阈值表。
