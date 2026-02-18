# WORKFLOW — ModelEval-Self（OPERATOR / 主控台编排者手册）

> Version: `1.4`
> Last Updated: `2026-02-19`
> Status: `active`

> **Role**：SG_OPERATOR（主控台 / 编排者）
>
> ```yaml
> EVAL_MODE: ORCHESTRATION_CONTROL
> ```

---

## 1) 架构拓扑与权限边界

**固定控制流**：`OPERATOR (Main) -> SPAWN -> sub0 (Reviewer) -> SPAWN -> sub1/sub2 (Executors)`

- **OPERATOR**：注入全局上下文、生成 `Run_ID`、挂起等待、执行轨道 2 终局验收。
  - **绝对禁止**：越权代跑 `sub1/sub2` 的底层评测命令；干预 `sub0` 的具体打分（轨道 1）。
- **sub0 (Reviewer)**：派发子任务、质询取证、提取物理母带（`.jsonl`）、填写轨道 1 评分。
  - **仅限**：调度子代，受控于 OPERATOR 的生命周期管理。

---

## 2) 环境锚定与上下文注入 (Context Injection)

OPERATOR 必须在测试启动前完成以下全局状态初始化，并作为系统级环境变量强制注入给 `sub0`：

1. **生成时序 ID (Run_ID)**：
   - 执行 `date -u +"%Y%m%d_%H%M"` 获取 UTC 时间锚点。
   - 构造 `Run_ID` 格式：`<Batch_ID>_M<Seq>`（例：`BATCH_20260219_1400_SelfEval_M1`）。
2. **锁定 Git 分支拓扑**：
   - 必须强制 `sub0` 与其子代使用统一分支：`self-audit/<Run_ID>/round<round>`。
3. **下发初始载荷 (Payload)**：
   - 向 `sub0` 派发任务时，指令必须包含完整参数表：`Run_ID`, `目标模型标识`, `SELF_AUDIT_BRANCH`, 以及强约束文件路径 (`WORKFLOW-ModelEval-Self-REVIEW.md`)。

---

## 3) 强同步锁与生命周期管理 (Lifecycle Synchronization)

为防止异步并发导致的失联与死锁，OPERATOR 必须对 `sub0` 实施严格的状态机控制：

### 3.1 阻塞等待协议 (Blocking Wait)
- 派发 `sub0` 后，OPERATOR 必须进入 `<STATE: SUSPEND_WAITING>`。
- **严禁静默休眠**：必须维持对 `sub0` 会话状态的轮询或维持系统级锁存。
- 唤醒事件：仅当 `sub0` 返回明确的 `ROUND1_CLOSED` 或 `ROUND2_CLOSED` 信号，且对应产物已落盘时，OPERATOR 才允许进行状态推进。

### 3.2 熔断与死锁恢复
- **指令超时 (Timeout)**：`sub0` 超过 15 分钟未返回 Checkpoint ACK。
  - **Action**：触发 `TIMEOUT_DEADLOCK`。立即 Kill `sub0`，记录 `Fail-Fast`。
- **崩溃 (Crash)**：`sub0` 异常退出且无归档。
  - **Action**：判定 `FAULT_EXEC_RUNTIME`。允许重试 1 次；若再败，终结测试。
- **时序倒置 (Inversion)**：`sub0` 在 R1 结束前请求 Spawn R2。
  - **Action**：强制拦截。注入纠偏指令，要求回退。

---

## 4) 轨道 2：编排质量验收 (Orchestration Audit)

当 `sub0` 完成所有流程并交付 `review_<Run_ID>_round<1|2>.md` 后，OPERATOR 负责最终验收（轨道 2），防范评审官 `sub0` 发生逻辑幻觉。

### 4.1 验收矩阵
OPERATOR 必须基于物理文件系统验证 `sub0` 的工作，而非听信其文本汇报：

1. **流程完整性 (Process Integrity)**：
   - 验证 `sub0` 是否严格执行了 `Challenge`（质询）。
   - 验证 `sub0` 的评分（D1-D5）是否遵循了 `SCORING-UNIVERSAL.md` 阈值。
2. **证据归档 (Artifact Archival)**：
   - 执行 `ls -l Audit-Report/<YYYY-MM-DD>/raw_logs/`，核对物理母带 `.jsonl` 是否存在且非空。
   - 验证 `transcript_*.md` 是否成功渲染。
3. **记录合规性 (Record Compliance)**：
   - 验证 `sub0` 是否在 Git 树中产生了有效的 commit (`git log --oneline`)。

### 4.2 最终报告篡写
OPERATOR 必须覆写 `sub0` 报告末尾的占位符区块：
```markdown
### 轨道 2：编排质量评定 (Orchestration Audit) - [Operator 专用]
- 流程完整性: <PASS / FAIL> (附注：是否执行 Challenge 与顺序控制)
- 证据归档: <PASS / FAIL / INCOMPLETE> (附注：物理日志数量与文件大小异常检测结果)
- 记录合规性: <PASS / FAIL> (附注：Git Commit 校验结果)
- **编排结论: <VALID / INVALID>** (若任一为 FAIL/INCOMPLETE，整体 INVALID，该模型测试作废)
```

---

## 5) Fail-Fast 裁决策略 (Operator 权限)

出现以下情况，OPERATOR 直接介入并终止当前测试批次：
- `sub0` 上报 `MODEL_ECHO_MISMATCH`（模型错配）且人工/策略明确不重试。
- `sub0` 陷入“归档逻辑死循环”（重复抓取错误时间窗的 session）。
- 物理节点磁盘空间耗尽或系统级环境异常（如 OpenClaw 框架崩溃）。

---

## 6) OPERATOR 执行防错清单 (Fuse Checklist)
- [ ] 已生成正确的 `Run_ID` 并注入时序锚点。
- [ ] 已将测试上下文（分支名、目标模型）无歧义地传递给 `sub0`。
- [ ] 派发 `sub0` 后，**已激活同步等待锁**，未提前结束当前对话回合。
- [ ] `sub0` 交付后，已通过 CLI 命令物理核验 `raw_logs/` 目录的真实性。
- [ ] 已完成“轨道 2”区块的验收与填写。