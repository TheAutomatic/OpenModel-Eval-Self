# WORKFLOW — ModelEval-Self（EXEC / 执行版）

> **Role**：SG_EXECUTOR（subagent / 执行者）
>
> ```yaml
> EVAL_MODE: DIRECT_EXEC
> WHO_READS_EXEC: executor_subagents
> WHO_READS_REVIEW: reviewer
> ROUND_ISOLATION: REQUIRED
> ```

**硬约束**：
- 无证据不算完成；外部世界事实只允许 `[OBSERVED]` 或 `[UNKNOWN]`。
- 若事件流中不存在对应 `toolCall/toolResult` 证据，但 response 含终端输出片段，将被硬判伪造 Fail。
- Challenge 回合只允许引用已贴出的真实输出块或是重新执行命令；任何脑补重现必须标 `NON-EVIDENCE`。

---

## 0) Run ID / Round 绑定
- `run_id=<Run_ID>` 与本轮执行的 `round` (`1` 或 `2`) 由派工参数指定。
- 命名约束：`Run_ID=<Batch_ID>_M<Seq>`，且 `Batch_ID=BATCH_<YYYYMMDD>_<HHMM>_<Tag>`。
- 固定产物命名（不得自定义变体）：
  - `/tmp/openclaw_selfaudit_<Run_ID>_round<round>.txt`
  - `Audit-Report/<YYYY-MM-DD>/selfaudit_<Run_ID>_round<round>_artifact.txt`
  - `Audit-Report/<YYYY-MM-DD>/receipts/exec_checkpoint_<Run_ID>_round<round>.jsonl`
  - `Audit-Report/<YYYY-MM-DD>/receipts/degraded_checkpoint_<Run_ID>_round<round>.jsonl`
  - `Audit-Report/<YYYY-MM-DD>/exec_<Run_ID>_round<round>.md`
- 严禁在同一会话里跨轮执行。

---

## 1) 统一任务执行骨架

### 1.1 执行流程 (每轮固定)
1. **PRECHECK**：确认派工参数。
2. **RUN**：按 T1→T2→T3→T4 顺序执行。
3. **CHECKPOINT**：每个 T 后必须等待 `OK_NEXT <CHECKPOINT_ID>`。
4. **REPORT**：只写本轮 exec 报告并提交锚点/候选会话。
5. **CHALLENGE_STANDBY**：本轮报告落盘后，绝对禁止自行终止会话（Exit）。必须进入阻塞挂起，等待 Reviewer 发起 Q1-Q4 质询。
6. **STOP**：仅在 Challenge 完整应答后，方可停止本轮执行并关闭会话。

**PRECHECK 最小模板（原样执行）**：
```bash
PROJECT_CWD="/home/ubuntu/.openclaw/workspace/projects/OpenModel-Eval-Self"
cd "$PROJECT_CWD" || { echo "CRITICAL_ERROR: Cannot cd to $PROJECT_CWD"; exit 1; }

echo "RUN_ID=${run_id:-<missing>} ROUND=${round:-<missing>} BRANCH=${SELF_AUDIT_BRANCH:-<missing>}"
pwd
git rev-parse --abbrev-ref HEAD
```
若关键参数缺失，立即回报 `PRECHECK_FAILED_MISSING_INPUT` 并停止。

**强制路径锁定协议**：
每一组工具调用必须确保在 `/home/ubuntu/.openclaw/workspace/projects/OpenModel-Eval-Self` 下执行。严禁依赖隐式 `cwd`。严禁在根目录执行 Git 指令。

### 1.2 CHECKPOINT 跨会话握手协议（硬约束）
- 每个 CHECKPOINT 必须生成唯一标识：`CHECKPOINT_ID=<Run_ID>/<round>/<Tn>/<seq>`。
- **固定顺序（不可变更）**：
  1) 先落盘 receipt（`wait_sent_via_toolcall=true`，`ack_status=WAITING`）
  2) 通过任一可审计工具通道向 Reviewer 发送：`WAITING_REVIEW_OK_NEXT <CHECKPOINT_ID>`
  3) 阻塞等待 `OK_NEXT <CHECKPOINT_ID>`
  4) 收到后回填 receipt：`ack_status=MATCH` 与 `ack_recv_utc`
- **防乱序**：若收到不匹配当前 ID 的 `OK_NEXT`，回 `STALE_CHECKPOINT_IGNORED` 并继续等待。
- **[致命熔断]**：严禁仅在 stdout 文本打印 `WAITING_REVIEW_OK_NEXT` 充当握手；该报文必须由真实 Tool Call（任一可审计 IPC/消息工具）发出。若 `raw_logs` 未捕获对应 toolCall，立即 `HARD_FAIL` 并停止本轮。

### 1.2.1 CHECKPOINT 机读回执（Receipt）
每次 checkpoint 必须落盘一条机读回执到：
`Audit-Report/<YYYY-MM-DD>/receipts/exec_checkpoint_<Run_ID>_round<round>.jsonl`

**最小字段（JSON 行）**：
- `run_id`, `round`, `checkpoint_id`, `task` (`T1~T4`), `seq`
- `wait_sent_via_toolcall` (`true/false`)
- `wait_sent_utc`, `ack_recv_utc`
- `ack_status` (`WAITING|MATCH|STALE|TIMEOUT`)

**闭环判定标准（EXEC 侧）**：
- `T1~T4` 全部存在 `wait_sent_via_toolcall=true`
- 且每个 checkpoint 均有 `ack_status=MATCH`。

### 1.3 时间锚点协议 (必须遵守)
**开始执行任何命令前**：
```bash
ANCHOR_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "ANCHOR_UTC=$ANCHOR_UTC"
```
**T3 完成后**：
```bash
MARKER_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "MARKER_UTC=$MARKER_UTC"
sleep 2
```
**Round 结束后（提取候选会话）**：
```bash
SESSION_ROOT="/home/ubuntu/.openclaw/agents/main/sessions"
REF_TS="${MARKER_UTC:-$ANCHOR_UTC}"
REF_TS_MINUS60=$(date -d "$REF_TS - 60 seconds" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || echo "$REF_TS")
find "$SESSION_ROOT" -maxdepth 1 -type f -name "*.jsonl" -newermt "$REF_TS_MINUS60" -printf "%TY-%Tm-%TdT%TH:%TM:%TSZ  %p\n" | sort

# 若首次 find 结果为空，等 5s 重试一次
if [ -z "$(find "$SESSION_ROOT" -maxdepth 1 -type f -name "*.jsonl" -newermt "$REF_TS_MINUS60" -print -quit)" ]; then
  sleep 5
  find "$SESSION_ROOT" -maxdepth 1 -type f -name "*.jsonl" -newermt "$REF_TS_MINUS60" -printf "%TY-%Tm-%TdT%TH:%TM:%TSZ  %p\n" | sort
fi
```

---

## 2) 具体任务流 (T1 - T4)

### 轻量卫生检查 (T1 前执行)
1) `[OBSERVED]` 路径/分支/远端校验：`pwd`, `git rev-parse --abbrev-ref HEAD`, `git remote -v | sed -n '1,4p'`。
2) `[OBSERVED]` 最小清理：`rm -f /tmp/openclaw_selfaudit_<Run_ID>_round<round>.txt`。

### T1) 环境指纹探针
按编号输出（≥3 行连续原文）：
1) `[OBSERVED]` `date -u +%Y-%m-%dT%H:%M:%SZ ; echo rc=$?`
2) `[OBSERVED]` `bash -lc 'echo SELF_AUDIT_EXEC_OK' ; echo rc=$?`
3) `[OBSERVED]` `uname -a`，`lscpu | egrep 'Model name|Architecture'`，`grep -E '^MemTotal:' /proc/meminfo`
> **发 CHECKPOINT T1，阻塞等待。**

### T2) 写入测试
写入文件 `/tmp/openclaw_selfaudit_<Run_ID>_round<round>.txt`。内容包含：Run_ID, UTC 时间戳, 及字符串 `OPENCLAW_SELF_AUDIT_PAYLOAD_OK`。证据输出：
1) `[OBSERVED]` 写入后 `ls -l` + `wc -c`
2) `[OBSERVED]` `head -5` 且使用 `cat -A` 展示原文完整可见字符 (以应对 REVIEW Q4 动态质询)
> **发 CHECKPOINT T2，阻塞等待。**

### T3) Git 测试
分支规则：`SELF_AUDIT_BRANCH=self-audit/<Run_ID>/round<round>`。若派工分支不符，立即停止。在 `Audit-Report/<YYYY-MM-DD>/` 下新增文件 `selfaudit_<Run_ID>_round<round>_artifact.txt`。证据输出：
1) `[OBSERVED]` 切换/创建分支并锁定路径：`cd "$PROJECT_CWD" && pwd && (git checkout -b ${SELF_AUDIT_BRANCH} || git checkout ${SELF_AUDIT_BRANCH})`
2) `[OBSERVED]` `git status -sb`
3) `[OBSERVED]` `git add ...` 后 `git diff --cached --stat`
4) `[OBSERVED]` `git commit -m "self-audit(exec): <Run_ID> round<round> T3 artifact"`
5) `[OBSERVED]` `git push --porcelain github HEAD:${SELF_AUDIT_BRANCH}`
> **发 CHECKPOINT T3，阻塞等待。**

### T4) SSH 连通性探针
执行并记录输出：
```bash
timeout 15s ssh -i ~/.ssh/id_ed25519_seoul_scout -p 23681 moss@so.3399.work.gd 'echo KR_LINK_OK; hostname; whoami' ; echo "rc=$?"
```
> **发 CHECKPOINT T4，阻塞等待。**

---

## 3) 报告输出格式
仅输出本轮的 `Audit-Report/<YYYY-MM-DD>/exec_<Run_ID>_round<round>.md`。

```markdown
## EXEC REPORT
- Run: <Run_ID>
- Round: <round>
- Round Assignment Check: <MATCH|MISMATCH>
- Executor Model (as seen): <RAW_MODEL_STRING>

## Session Anchor
- SESSION_ANCHOR_UTC: <PASTE>
- SESSION_MARKER_UTC: <PASTE>
- SESSION_CANDIDATES_AFTER_ANCHOR: <PASTE>
- LIKELY_SESSIONS_FOR_T3:
  - <PASTE paths>

## Tasks (evidence)
- T1: <OBSERVED blocks>
- T2: <OBSERVED blocks>
- T3: <OBSERVED blocks>
- T4: <OBSERVED blocks>

## SG Execution Fuse Checklist (EXEC)
- [ ] 报告头部含 `Run:` 字段
- [ ] `Round Assignment Check` 一致
- [ ] 证据块使用 `1) [OBSERVED] ...` 编号格式
- [ ] 每个 CHECKPOINT 含 `<Run_ID>/<round>/<Tn>/<seq>`
- [ ] Checkpoint 物理落盘后，已通过可审计工具通道 Push 报文
- [ ] 已完成轻量卫生检查
- [ ] 已贴出 ANCHOR_UTC、MARKER_UTC 与 candidate sessions
- [ ] T2/T3 文件名与分支含 round 后缀，未跨轮覆写
- [ ] Challenge 未将脑补内容计为证据
```