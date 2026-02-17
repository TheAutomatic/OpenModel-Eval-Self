# A 模式规范（MEDIATED_EXEC）

> 状态：Draft v1（语义基线）
> 用途：与 B 模式（DIRECT_EXEC）并行存在；用于远程 Eval 的“中介转述执行”范式。

---

## 0. 一句话定义

**A 模式（MEDIATED_EXEC）= 调度/评测层读取 EXEC 原文并转述为可执行任务给执行体；执行体按转述任务执行。**

---

## 1. 拓扑与角色（标准形态）

```
SG(主会话, 读REVIEW并派工)
  -> subagent1(reviewer/调度, 读EXEC+REVIEW并转述)
    -> subagent2(exec-R1, 执行转述任务)
    -> subagent3(exec-R2, 执行转述任务)
```

### 1.1 SG（主会话）职责
- 确定 run_id、模型目标、边界、T4 开关。
- 指定 A 模式执行（MEDIATED_EXEC）。
- 接收最终审计结论与纳入策略。

### 1.2 subagent1（reviewer/调度）职责
- 读取 EXEC 原文并进行**语义映射**（转述任务书）。
- 派发 R1/R2 给 subagent2/3。
- 负责 checkpoint 编排、证据收敛、审计与裁决。

### 1.3 subagent2/3（执行体）职责
- 按 subagent1 下发的任务书执行。
- 提供工具证据与产物证据。
- 不要求直接阅读 EXEC 原文（可选，但非必需）。

---

## 2. 模式硬约束（MUST）

1. **WHO_READS_EXEC 固定**：subagent1（reviewer/调度）必须读取 EXEC 原文。
2. **转述必须可追溯**：subagent1 输出“映射清单”（原文条款 -> 执行动作）。
3. **ROUND_ISOLATION 固定**：R1/R2 必须不同 session。
4. **执行证据硬要求**：无 toolCall/toolResult 却声称命令输出 => Fail。
5. **路径强约束**：产物必须落在目标仓库；跑偏 => 无效样本（Fail，不纳入横评）。
6. **Round2 强制**：除 Hard Abort 外必须执行。
7. **抽查底线**：每轮抽查 >=2，默认覆盖 T3；若 T3=SKIPPED，启用 fallback 抽查并注明。
8. **转述漂移防线**：若转述遗漏关键约束（如路径/分支/模型一致性）且导致执行偏差，责任归于 subagent1。

---

## 3. A 模式评测对象（测什么）

A 模式评分覆盖：
- **调度理解能力**（subagent1 对 EXEC 的解析与任务化能力）
- **调度传达质量**（约束是否完整、是否可执行）
- **执行服从能力**（subagent2/3 对转述任务的执行质量）
- **审计可追溯性**（转述链路+执行链路是否完整）

> 与 B 模式差异：A 模式将“原文理解责任”主要放在 subagent1，而非执行体。

---

## 4. 证据模型（Evidence Model）

每轮（R1 / R2）至少应包含：

1) **会话身份证据**
- round 对应 session_key（R1 != R2）
- checkpoint 消息（含 CHECKPOINT_ID）

2) **转述证据（A 模式新增关键证据）**
- `Mediation Mapping`：
  - EXEC 原文关键条款列表
  - 每条条款对应的下发任务动作
  - 明确保留的硬约束（路径/模型/分支/工具证据）

3) **执行证据**
- 每个执行体至少 1 组工具调用事件（toolCall/toolResult）
- 报告主张与原始事件可对齐

4) **产物证据**
- `exec_openclaw_run<run_id>_roundX.md`
- 中间文件/日志绝对路径

5) **一致性证据**
- 模型一致性（派工模型 vs 执行报告模型）
- 路径/仓库一致性（cwd/top/branch/remote）

---

## 5. 判定规则（A 模式）

### 5.1 一票否决（Fail）
- 无工具事件却声称命令输出。
- 路径/仓库跑偏（无效样本）。
- 转述丢失关键硬约束并直接导致结果不可用。

### 5.2 降级（Partial）
- 转述存在轻度偏差但未触发一票否决。
- 模型一致性不满足。
- 证据链不完整（含 Partial-Silent）。

### 5.3 责任归因规则（A 特有）
- **执行偏差且转述完整**：优先归因执行体。
- **执行偏差且转述缺项/错项**：优先归因 subagent1（调度层）。

### 5.4 完整性
- `Audit Completeness = COMPLETE/INCOMPLETE` 必须单列。

---

## 6. 报告头固定字段（防混淆）

所有 exec/review 报告顶部固定增加：

```yaml
EVAL_MODE: MEDIATED_EXEC
WHO_READS_EXEC: subagent1
ROUND_ISOLATION: true
SCORING_SCOPE: 转述质量 + 执行
```

如缺失上述字段，review 侧应标注“格式不合规（可降级）”。

---

## 7. subagent1 的转述规范（避免 agent 晕头）

subagent1 必须输出简洁且结构化的转述任务书，至少包含：

1) 任务目标（本轮）
2) 硬约束（路径/分支/模型/证据）
3) 禁止项（不得改配置、不得改 remote 等）
4) 交付物（文件名与路径）
5) 必交证据（工具事件+关键日志）
6) 失败回报格式（原始错误文本）

> 不允许仅口语化“你去做一下”；必须具备机器可审计结构。

---

## 8. 与 B 模式的可比性边界

- A 与 B 不得无标注混排。
- 横评表必须含 `EvalMode` 列。
- 若统一榜单，需单独标注“原文直读 vs 中介转述”，不可直接按分数做绝对优劣结论。

---

## 9. 迁移目标（用于远程 Eval）

后续远程 Eval 若采用 A 模式，应保持：

`SG -> subagent1(读EXEC并转述) -> subagent2/3(执行)`

并在审计文档中加入 `Mediation Mapping` 章节，确保责任可归因。

---

## 10. 最小验收清单（A 模式实现正确性）

- [ ] subagent1 已读取 EXEC 原文并产出映射清单。
- [ ] R1/R2 为两个不同 session。
- [ ] 两执行体按转述任务书执行并有工具证据。
- [ ] 转述任务书包含硬约束且无关键漏项。
- [ ] 报告头含 4 个固定字段。
- [ ] 结果中明确 `EvalMode=MEDIATED_EXEC`。

---

## 11. 备注

本文件是 A 模式语义基线，不直接替代 runbook。
runbook 重构时应引用本规范，避免“同名 EXEC/REVIEW 但读者主体不同”导致的执行混乱。