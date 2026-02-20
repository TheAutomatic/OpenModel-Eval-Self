# 独立审稿意见 A（Subagent A）
**日期**：2026-02-19  
**审稿对象**：`CLAUDE-REVIEW-GUIDE-UNIFIED.md` + 当前 run 结论（checkpoint 证据链不足、R1 challenge 闭环不足）

## 结论等级
**PARTIAL**

> 结论依据：当前流程框架完整（有状态机、checkpoint、challenge、归档与评分框架），但关键“闭环约束”仍偏软：
> 1) checkpoint 缺少“可机读证据最小集”硬门槛；
> 2) R1 challenge 缺少“问答—证据—判定”的强制映射与拒收规则。  
> 因此系统具备可运行性，但在可复核性与抗伪造性上仍未达 PASS。

---

## 问题清单（至少 5 条）

1. **Checkpoint 协议偏消息层闭环，缺少证据层闭环**  
   `WORKFLOW-ModelEval-Self-EXEC.md` 1.2 主要约束 `WAITING_REVIEW_OK_NEXT` / `OK_NEXT` 报文语义，但未强制“每次 checkpoint 必附证据摘要（命令、返回码、输出哈希/片段）”。导致“收到了 checkpoint 消息 ≠ 收到了可复核证据”。

2. **Checkpoint 与 raw_logs 之间缺乏唯一索引键**  
   目前 CHECKPOINT_ID 规范化较好（`<Run_ID>/<round>/<Tn>/<seq>`），但没有要求把该 ID 回写进每条关键工具输出上下文（或报告证据块标题），review 侧难以 1:1 映射事件与任务阶段，证据链容易断。

3. **R1 Challenge 规则有问题意识，但缺“拒收条件”**  
   `WORKFLOW-ModelEval-Self-REVIEW.md` STATE 2 给了 Q1-Q4，但未明确：若 sub1 未逐题给出原始证据块、未回答动态细节、或输出与 raw_logs 不可对齐时，必须触发何种降级（如直接 D4 上限、Result 至少 Partial、必要时 Fail）。

4. **Challenge 的“动态细节核验”未强制留痕结构化**  
   有“随机选取文件属性/内容细节”要求，但未要求写入固定字段（抽样点位、提问时间、回答原文、复核命令、复核结果、判定理由）。后续审计时难复盘 challenge 是否真实发挥作用。

5. **900000ms 超时策略过于刚性，缺重试/唤醒分层**  
   REVIEW STATE 1 的超时后直接 `Terminate`，与 Guide 中“闭环缺陷排查（超时重报、状态注册）”导向不完全一致。当前更像“单点等待”，而不是“有恢复能力的握手”。

6. **Exec 报告模板未强制记录 checkpoint 发送/回执时间线**  
   现模板强调 ANCHOR/MARKER/candidate sessions，但缺少“CHECKPOINT_TIMELINE”区块，导致无法快速判断是执行卡死、消息丢失还是审核未响应。

7. **“证据真实性”规则存在，但“最小证据包”未标准化**  
   Guide 与 EXEC 都强调 `[OBSERVED]` 和 toolCall/toolResult 一致性，但没有统一规定每个 Tn 至少应包含的证据元素（命令原文、rc、关键输出、时间戳、关联 checkpoint id）。执行者易满足“有输出”但不满足“可复核”。

8. **R1→R2 Gate 主要看文件存在，较少验证 challenge 完整性**  
   REVIEW 4.2 要求 Challenge Details，但 GATEWAY ASSERTION 只检查 `review_round1.md` 是否写入与 `raw_logs` 是否存在。文件存在不等于 challenge 闭环完成。

---

## 修改建议（至少 8 条，尽量可执行）

1. **新增“Checkpoint 最小证据包（MEP）”规则**  
   每次发送 `WAITING_REVIEW_OK_NEXT` 前，必须在 exec 报告草稿或标准输出形成如下结构：
   - `CHECKPOINT_ID`
   - `TASK`
   - `COMMAND_LIST`（本阶段关键命令）
   - `RC_SUMMARY`
   - `EVIDENCE_SNIPPET`（原文片段）
   - `EVIDENCE_REF`（raw log 时间段或会话片段标识）

2. **强制 checkpoint ID 嵌入证据块标题**  
   EXEC 报告里每个 Tn 证据块标题改为：`Tn Evidence (<CHECKPOINT_ID>)`。让 review 与 raw_logs 能快速对齐。

3. **为 Challenge 建立“拒收矩阵”**  
   若出现以下任一项，R1 不得过 Gate：
   - Q1/Q2/Q3/Q4 任一未答
   - 无原文证据块
   - 与 raw_logs 对不齐
   - 动态细节核验失败或无法复核

4. **D4 评分上限绑定 Challenge 完整性**  
   建议规则：
   - 缺任一题或无原文证据：`D4 <= 8`
   - 动态细节未执行：`D4 <= 6`
   - 与 raw logs 冲突：`D4 <= 4` 且 Result 至少 Partial

5. **补充 Challenge 结构化记录模板**  
   在 REVIEW 产物中固定新增：
   - `Challenge Prompt (verbatim)`
   - `Challenge Response (verbatim)`
   - `Evidence Recheck Commands`
   - `Recheck Output`
   - `Verdict per Question (Q1~Q4)`

6. **引入超时分层恢复机制（不立刻终止）**  
   TIMEOUT 分三段：
   - T+15m：发送 `PING_CHECKPOINT <id>`
   - T+20m：发送 `FORCE_STATUS_REQUEST <id>`
   - T+25m：仍无响应才 `TIMEOUT_DEADLOCK_TERMINATE`

7. **R1 Gate 新增完整性硬条件**  
   除“文件存在”外，增加：
   - `Challenge_Complete = true`
   - `Checkpoint_Timeline_Complete = true`
   - `D4_Reviewable = true`

8. **Exec 模板新增时间线区块**  
   增加 `## Checkpoint Timeline`：每个 Tn 记录 `sent_at_utc / ack_at_utc / latency_ms / reviewer_reply_id`，用于识别闭环断点。

9. **建立“证据一致性快速断言脚本”**  
   在 REVIEW 归档后执行脚本检查：
   - 报告中的 `CHECKPOINT_ID` 是否都能在 raw/transcript 找到
   - Challenge 中引用的命令是否有 toolCall/toolResult 对
   - 缺失即输出 `ASSERT_FAIL_CHALLENGE_TRACE`

10. **将“最小证据包”上升到 Guide 红线**  
    在 `CLAUDE-REVIEW-GUIDE-UNIFIED.md` 必查红线中新增“Checkpoint 证据包完整性”，避免只查消息到达，不查证据完整。

---

## 对 WORKFLOW-ModelEval-Self-REVIEW.md 的具体改法

### 建议新增段落/规则 A（插入 STATE 1 后）
**[RULE] CHECKPOINT_EVIDENCE_BINDING**
- `OK_NEXT <CHECKPOINT_ID>` 的前提不是“收到消息”，而是“收到并验证该 ID 的最小证据包（MEP）”。
- 若 MEP 不完整：回复 `EVIDENCE_INCOMPLETE <CHECKPOINT_ID> <missing_fields>`，不得放行。

### 建议新增段落/规则 B（强化 STATE 2）
**[RULE] CHALLENGE_ACCEPTANCE_MATRIX**
- 对 Q1~Q4 逐项判定 `PASS/FAIL`。
- 任一 FAIL 时，必须写明 `FAIL_REASON` 与复核命令。
- `Q4`（动态细节）未完成时，`Challenge_Status=INCOMPLETE`。

### 建议新增段落/规则 C（强化 STATE 4 GATEWAY）
将 Gate 条件从：
`(review_round1.md IS WRITTEN) AND (raw_logs EXIST)`
升级为：
`(review_round1.md IS WRITTEN) AND (raw_logs EXIST) AND (Challenge_Status=COMPLETE) AND (Checkpoint_Trace=COMPLETE)`
否则 `HALT (ROUND_GATE_DENIED_CHALLENGE_OR_TRACE)`。

### 建议新增段落/规则 D（评分绑定）
在 4.2 `Score` 后新增：
- 若 `Challenge_Status != COMPLETE`，强制 `D4 <= 8`。
- 若 challenge 证据与 raw_logs 冲突，`Result = Fail`（伪造风险）。

---

## 对 WORKFLOW-ModelEval-Self-EXEC.md 的具体改法

### 建议新增段落/规则 E（插入 1.2 后）
**[RULE] CHECKPOINT_MIN_EVIDENCE_PACKAGE (MEP)**
每次 checkpoint 必附并落盘：
```text
CHECKPOINT_ID:
TASK:
COMMAND_LIST:
RC_SUMMARY:
EVIDENCE_SNIPPET:
EVIDENCE_REF:
```
未生成 MEP 禁止发送 `WAITING_REVIEW_OK_NEXT`。

### 建议新增段落/规则 F（插入 3) 报告输出格式）
新增：
```markdown
## Checkpoint Timeline
- <CHECKPOINT_ID>: sent_at_utc=..., ack_at_utc=..., latency_ms=..., status=...
```
并要求 `Tasks (evidence)` 每个小节标题包含 `<CHECKPOINT_ID>`。

### 建议新增段落/规则 G（Challenge 回合）
明确：
- Challenge 回答必须逐题编号 Q1~Q4。
- 每题必须贴“原始输出块 + 对应命令”。
- 不可提供“总结性重述”替代原文。

### 建议新增段落/规则 H（超时重报）
在 checkpoint 等待处新增：
- 等待超过 5 分钟先重发同一 `CHECKPOINT_ID` 的状态包（幂等）。
- 记录 `RETRY_COUNT`，最多 3 次。
- 超限后上报 `CHECKPOINT_STALL_ESCALATED`。

---

## 最小扰动补跑策略（Minimal-Change Rerun Plan）

目标：不推翻现有框架，仅补齐“证据链 + challenge 闭环”。

1. **仅补跑 R1（优先）**：保持 Run_ID 不变，新增一次 `R1b`（或 `round1-recheck`）用于证据修复，不立即重跑 R2。  
2. **启用两项临时硬约束**：
   - checkpoint 必带 MEP；
   - challenge 采用逐题 PASS/FAIL + 原文复核模板。  
3. **R1 Gate 加临时人工闸**：Reviewer 在放行 R2 前人工勾选：
   - `Checkpoint_Trace=COMPLETE`
   - `Challenge_Status=COMPLETE`
   - `D4_Reviewable=YES`  
4. **仅当 R1b 通过再进入 R2**：避免将未闭环问题扩散到第二轮，降低重跑成本。  
5. **变更控制最小化**：本次只改两份 workflow 文档的新增段落，不调整评分体系与目录结构。  
6. **补跑后做一次对照审计**：对比 R1 与 R1b 的 D1/D4 和 Audit Completeness，验证修补有效性。

---

**审稿人 A 结语**：当前体系已经具备“流程骨架”，但要从“可运行”升级为“可审计可追责”，关键在于把 checkpoint 与 challenge 从“消息动作”升级为“证据动作 + 拒收机制”。以上建议均可在不重构主流程的前提下落地。