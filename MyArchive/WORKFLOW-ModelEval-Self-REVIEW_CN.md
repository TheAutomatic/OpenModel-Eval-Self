# 工作流 — ModelEval-Self-REVIEW (v1.4) 中文版

> 版本: `1.4`
> 最后更新: `2026-02-19`

> **角色**: SG_REVIEWER (sub0 / 评审官)
> **拓扑结构**: `OPERATOR` -> `sub0` -> `sub1(R1)` / `sub2(R2)`
> **模式**: 直接执行 / 状态机

---

## [STATE 0] 初始化与负载检查 (INIT & PAYLOAD_CHECK)

**触发条件 (TRIGGER)**: `OPERATOR` 派发 `sub0`。
**断言 (ASSERTIONS)**:
- 参数必须包含: `<Run_ID>`, `<TARGET_MODEL>`, `<SELF_AUDIT_BRANCH>`。
- 否则执行: `ACTION -> Terminate (PRECHECK_FAILED_MISSING_INPUT)`。
**状态迁移 (TRANSITION)**: `GOTO [STATE 1]`

---

## [STATE 1] 第一轮执行 (sub1) (ROUND 1 EXECUTION)

**触发条件 (TRIGGER)**: 进入 `STATE 1`。
**动作 1 (ACTION 1)**: 生成 (Spawn) `sub1`。注入参数表 (R1)。
**动作 2 (ACTION 2)**: `EXEC process(action=poll, timeout_ms=900000)` -> 进入 `[SUSPEND_WAITING]` (挂起等待) 状态。

### [事件] 收到跨会话消息 (EVENT: INTER_SESSION_MESSAGE_RECEIVED)
**有效负载 (PAYLOAD)**: `WAITING_REVIEW_OK_NEXT <CHECKPOINT_ID>`
- **条件 A (匹配 - MATCH)**: `CHECKPOINT_ID` == `<run_id>/1/<Tn>/<seq>`
  - `动作 (ACTION)`: 回复 `OK_NEXT <CHECKPOINT_ID>`
  - `状态迁移 (TRANSITION)`: 若 `Tn` == `T4`, 释放 `[SUSPEND_WAITING]`, `GOTO [STATE 2]`。否则保持挂起。
- **条件 B (陈旧 - STALE)**: `CHECKPOINT_ID` 为历史/已处理序号
  - `动作 (ACTION)`: 回复 `STALE_CHECKPOINT_IGNORED <CHECKPOINT_ID>`
  - `状态迁移 (TRANSITION)`: 保持 `[SUSPEND_WAITING]`。
- **条件 C (超时 - TIMEOUT)**: 超过 900000ms 未收到匹配报文
  - `动作 (ACTION)`: 记录 `TIMEOUT_DEADLOCK`
  - `状态迁移 (TRANSITION)`: 强制终止 `Terminate`。

---

## [STATE 2] 第一轮质询 (ROUND 1 CHALLENGE)

**触发条件 (TRIGGER)**: `STATE 1` 释放。
**动作 (ACTION)**: 向 `sub1` 发送固定格式质询：
```text
Q1: 请用一句话指出 T3 的 commit id、push 分支名，并贴出输出原文各1段。
Q2: 立刻执行只读命令并贴原始输出: `git rev-parse HEAD`, `git branch --show-current`, `ls -l /tmp/openclaw_selfaudit_<Run_ID>_round1.txt | cat`.
Q3: 若有异常请按“现象->原因->影响->动作”回答；若无写“NO_ANOMALY”。
Q4 (动态细节): sub0 必须根据 sub1 报告的 T2 内容，随机选取一个文件属性或内容细节进行核验（例：请指出该文件的第 X 个字符或精确字节数）。
```
**状态迁移 (TRANSITION)**: 等待 `sub1` 回复 -> 收到后 `GOTO [STATE 3]`。

---

## [STATE 3] 第一轮归档与审计 (ROUND 1 ARCHIVAL & AUDIT)

**触发条件 (TRIGGER)**: 收到 Challenge (质询) 回复。
**动作 (ACTION)**: 本地执行数据管道脚本 (Bash)。

```bash
RUN_ID="<Run_ID>"
ROUND="round1"
REF_TS="<从 EXEC 复制 SESSION_ANCHOR_UTC>"
ROUND1_END_UTC="<可选: round1 最后一个任务点的 utc>" # R2 归档时填入，用于物理隔离 R1
SESSION_ROOT="/home/ubuntu/.openclaw/agents/main/sessions"
OUT_DIR="Audit-Report/$(date -u +%Y-%m-%d)"
RAW_DIR="$OUT_DIR/raw_logs"
mkdir -p "$RAW_DIR"

REF_TS_MINUS60=$(date -d "$REF_TS - 60 seconds" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || echo "$REF_TS")
CANDIDATES=$(find "$SESSION_ROOT" -maxdepth 1 -type f -name "*.jsonl" -newermt "$REF_TS_MINUS60" ${ROUND1_END_UTC:+-newermt "$ROUND1_END_UTC"} -print0 | xargs -r -0 ls -1t | head -n 3)

[ $(echo "$CANDIDATES" | sed '/^$/d' | wc -l) -lt 2 ] && CANDIDATES=$(find "$SESSION_ROOT" -maxdepth 1 -type f -name "*.jsonl" -newermt "$(date -d "$REF_TS - 120 seconds" +"%Y-%m-%dT%H:%M:%SZ")" ${ROUND1_END_UTC:+-newermt "$ROUND1_END_UTC"} -print0 | xargs -r -0 ls -1t | head -n 3)

echo "$CANDIDATES" | while read -r f; do
  [ -z "$f" ] && continue
  bn="$(basename "$f")"
  cp "$f" "$RAW_DIR/raw_${RUN_ID}_${ROUND}_${bn}"
  python3 scripts/transcript_scalpel.py "$f" -o "$OUT_DIR/transcript_${RUN_ID}_${ROUND}_${bn}.md" --title "Transcript: ${RUN_ID} ${ROUND} (${bn})" || echo "TRANSCRIPT_GENERATION_FAILED" > "$OUT_DIR/transcript_${RUN_ID}_${ROUND}_${bn}.md"
done

# 断言: JSONL 转义检查 (ASSERTION: JSONL Escaping Check)
grep -nE "git[[:space:]]+commit" $RAW_DIR/raw_${RUN_ID}_${ROUND}_* || echo "[ASSERT_FAIL] MISSING_COMMIT"
grep -nE "git[[:space:]]+push" $RAW_DIR/raw_${RUN_ID}_${ROUND}_* || echo "[ASSERT_FAIL] MISSING_PUSH"

# UUID 唯一性核验 (物理证据提取)
grep -h "\"uuid\":" $RAW_DIR/raw_${RUN_ID}_${ROUND}_* | sort | uniq -c
```

**断言处理 (ASSERTION RESOLUTION)**: 
- 若归档文件数为 0 -> `D1_MAX_LIMIT = 4`, 标记 `NO_SESSION_EVIDENCE` (无会话证据)。
- 若 `ASSERT_FAIL` 触发 -> `Audit Completeness = INCOMPLETE` (审计完整性 = 不完整)。
- UUID 冲突检测 -> 若与历史 Session UUID 相同，标记 `SHARED_SESSION` (共享会话)。

**状态迁移 (TRANSITION)**: `GOTO [STATE 4]`

---

## [STATE 4] 第一轮裁决与网关 (ROUND 1 VERDICT & GATEWAY)

**触发条件 (TRIGGER)**: 归档管道执行完毕。
**动作 (ACTION)**: 渲染产物文件 `Audit-Report/<YYYY-MM-DD>/review_<Run_ID>_round1.md`。

### 4.1 快速失败仲裁矩阵 (FAIL-FAST ARBITRATION MATRIX)
| 条件 (If) | 动作 (Then) |
| :--- | :--- |
| `sub1` 声称有工具输出 **且** `raw_logs` 无对应 `toolCall/Result` | `Result = Fail` (硬判伪造) |
| `sub1` Model_ID 回显与 `<TARGET_MODEL>` 不符 | `Result = Partial / Fail`, 标记 `MISMATCH` (不匹配) |
| 物理归档量不足 / JSONL 正则断言失败 | 标记 `Audit Completeness = INCOMPLETE` (审计完整性 = 不完整) |

### 4.2 产物模板 (ARTIFACT TEMPLATE)
**必须包含 (MUST INCLUDE)**:
1. `TL;DR`: 包含 Run_ID, Model consistency (模型一致性), Task T1-T4 判定, Sampling paths (抽样路径)。
2. `Score` (得分): 严格输出 D1-D5 (0-20), Total (0-100), Rating (S/A/B/C/F)，基于 `SCORING-UNIVERSAL.md`。
3. `Challenge Details` (质询细节): Q/A/D4 原因。
4. `Orchestration Audit (Track 2)` (编排审计 - 轨道 2): 保留未填写占位符供 OPERATOR 覆写。

**第一轮终点记录 (ROUND 1 ENDPOINT RECORDING)**:
- **动作 (ACTION)**: 必须记录 `sub1` 最后一个报文的 UTC 时间戳，并保存为 `ROUND1_END_UTC` 以供 R2 物理隔离使用。

**网关断言 (GATEWAY ASSERTION) (R1 -> R2)**:
`IF (review_round1.md IS WRITTEN) AND (raw_logs EXIST)` -> `TRANSITION GOTO [STATE 5]`
`ELSE` (否则) -> `HALT (ROUND_GATE_DENIED)` (挂起 - 轮次网关拒绝)

---

## [STATE 5] 第二轮执行 (sub2) (ROUND 2 EXECUTION)

**触发条件 (TRIGGER)**: R1 网关通过。
**动作 0 (ACTION 0)**: 强制重置上下文。sub0 必须确保后续所有归档脚本中的 ROUND="round2" 且相关路径/变量已更新。
**动作 1 (ACTION 1)**: 生成 (Spawn) `sub2`。注入参数表 (R2)。
**动作 2 (ACTION 2)**: 激活 `[SUSPEND_WAITING]` (挂起等待)。
*(逻辑循环 `STATE 1` 至 `STATE 4`，覆盖 `round2`)*

**BASH 去重 (R2 特有) (BASH DEDUPLICATION)**:
Bash 脚本中 `CANDIDATES` 的 `find` 命令需增加 `-newermt "$ROUND1_END_UTC"` 参数，以隔离 R1 历史日志。

**终止 (TERMINATION)**:
`ROUND 2` 报告落盘并执行 `git commit/push` 后，通知 `OPERATOR` 接收控制权。`sub0` 退出。
``` `````