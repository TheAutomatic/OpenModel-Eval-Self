# B 模式规范（DIRECT_EXEC）

> 状态：Draft v1（语义基线）
> 用途：先固定评测语义，后续 runbook 重构必须与本规范对齐。

---

## 0. 一句话定义

**B 模式（DIRECT_EXEC）= 被评测执行体自己读取 EXEC 原文并执行；调度/审计层不做任务语义转述。**

---

## 1. 拓扑与角色（当前目标形态）

```
SG(主会话, 读REVIEW并派工)
  -> subagent1(reviewer/调度, 读REVIEW, 只调度与审计)
    -> subagent2(exec-R1, 自己读EXEC原文)
    -> subagent3(exec-R2, 自己读EXEC原文)
```

### 1.1 SG（主会话）职责
- 设定 run_id、模型、边界、是否启用 T4。
- 下发 REVIEW 框架给 subagent1。
- 最终接收审计结论并决策（是否纳入横评）。

### 1.2 subagent1（reviewer/调度）职责
- 只做：派发、收敛、抽查、裁决。
- 不做：将 EXEC“翻译”为简化步骤再喂给执行体。
- 维护 checkpoint 配对与异步乱序防护。

### 1.3 subagent2/3（被评测执行体）职责
- 各自独立读取 EXEC 原文。
- 各自独立执行并产出对应 round 报告。
- 各自提交可审计证据（工具事件+产物路径+关键约束命中）。

---

## 2. 模式硬约束（MUST）

1. **WHO_READS_EXEC 固定**：只能是 subagent2/3。
2. **ROUND_ISOLATION 固定**：R1/R2 必须不同 session。
3. **REVIEWER 不转述 EXEC 语义**：可提示“按原文执行”，不可改写成替代任务书。
4. **每轮必须有工具证据**：无 toolCall/toolResult 却声称命令输出 => Fail。
5. **路径强约束**：产物必须落在 self-repo，跑偏到 workspace 根仓库 => 无效样本（Fail，不纳入横评）。
6. **Round2 强制**：除 Hard Abort 外必须执行。
7. **抽查底线**：每轮抽查 >=2，默认覆盖 T3；若 T3=SKIPPED，执行 fallback 抽查并显式标注原因。

---

## 3. B 模式评测对象（测什么）

B 模式评分覆盖：
- **原文理解能力**：执行体对 EXEC 约束的识别与遵守。
- **执行正确性**：工具调用、命令结果、文件产物一致性。
- **审计可追溯性**：checkpoint、会话锚点、证据链完整度。

> 这与 A 模式（中介转述）不同：A 模式会引入“转述质量”变量，B 模式尽量移除该变量。

---

## 4. 证据模型（Evidence Model）

每轮（R1 / R2）至少应包含：

1) **会话身份证据**
- round 对应 session_key（R1 != R2）
- checkpoint 消息（含 CHECKPOINT_ID）

2) **执行证据**
- 至少 1 组工具调用事件（toolCall/toolResult）
- 与报告中关键主张对应的原始片段（可抽查）

3) **产物证据**
- `exec_openclaw_run<run_id>_roundX.md`
- 相关中间文件或日志路径（绝对路径）

4) **一致性证据**
- 模型一致性（派工模型 vs EXEC 报告模型）
- 路径/仓库一致性（cwd/top/branch/remote）

---

## 5. 判定规则（B 模式）

### 5.1 一票否决（Fail）
- 无工具事件却声称命令输出。
- 产物落盘到错误仓库/路径（无效样本）。
- 关键约束被明确违反且无可接受补救。

### 5.2 降级（Partial）
- 模型一致性不满足（例如派工是 pro-high，报告自述是 flash）。
- 证据不完整但未触发一票否决。
- 发生 Partial-Silent（有工具调用但关键输出被吞）且未完成补救。

### 5.3 完整性
- `Audit Completeness = COMPLETE/INCOMPLETE` 必须单独给出，不与分数混写。

---

## 6. 报告头固定字段（防混淆）

所有 exec/review 报告顶部固定增加：

```yaml
EVAL_MODE: DIRECT_EXEC
WHO_READS_EXEC: subagent2/subagent3
ROUND_ISOLATION: true
SCORING_SCOPE: 原文理解 + 执行
```

如缺失以上字段，review 侧应标记为“格式不合规（可降级）”。

---

## 7. reviewer 与 exec 的边界（关键）

### reviewer 可以做
- 指定 run_id、round 分工、checkpoint 节奏。
- 要求执行体“直接读取 EXEC 原文”。
- 抽查证据、判分、裁决。

### reviewer 不可以做
- 将 EXEC 改写成“摘要版任务书”替代原文。
- 将自身推理内容注入为执行体的“额外隐式要求”。
- 代替执行体完成应由执行体完成的关键步骤。

---

## 8. 与 A 模式的可比性边界

- A 与 B 评分结果不得无标注混排。
- 横评表必须包含 `EvalMode` 列（DIRECT_EXEC / MEDIATED_EXEC）。
- 若需统一榜单，需先定义换算或单独分组，不得直接相减比较。

---

## 9. 迁移目标（后续）

当 runbook 核心问题修复后，按本规范收敛为：

`subagent1(reviewer) -> subagent2(R1 direct exec) + subagent3(R2 direct exec)`

并保留 smoke 作为“变更后回归”手段，而非每次正式评测前置步骤。

---

## 10. 最小验收清单（本规范是否被正确实现）

- [ ] 两个 round 的执行体是两个不同 session。
- [ ] 两个执行体都显式按原文 EXEC 执行。
- [ ] reviewer 未提供替代语义任务书。
- [ ] 每轮均有工具证据与产物证据。
- [ ] 报告头含 4 个固定字段。
- [ ] 结果中明确 `EvalMode=DIRECT_EXEC`。

---

## 11. 备注

本文件是“语义基线文档”，不是最终 runbook。
runbook 改动应引用本文件作为上位约束，避免同名 EXEC/REVIEW 的语义漂移。