# WORKFLOW — ModelEval-Self（OPERATOR / 主会话决策层）

> Version: `1.2`
> Last Updated: `2026-02-18`
> Status: `active`

> 适用对象：Operator（你）+ 主会话助手（我）
>
> 目的：只定义“评测目标、约束、决策与验收规则”，不承载执行细节。
>
> 执行细节请看：
> - REVIEW：`WORKFLOW-ModelEval-Self-REVIEW.md`（给 sub0 编排/评审）
> - EXEC：`WORKFLOW-ModelEval-Self-EXEC.md`（由执行体执行）

---

## 1) 本层职责（Operator 层）

1. 选择本次评测模型（单模型或多模型串行）。
2. 下发任务给 sub0（review 执行者），要求其严格按 REVIEW 执行。
3. 审批关键策略变化（如 T4_REQUIRED、模型匹配规则、重派上限）。
4. 对最终结果做裁决（继续下一模型 / 重跑 / 终止）。

> 本层不直接写执行证据，不替代 REVIEW/EXEC 跑任务。

---

## 2) 标准执行拓扑（必须）

单模型评测固定拓扑：
- `Operator(SG主会话) -> sub0(reviewer) -> sub1(exec round1) -> sub2(exec round2)`

执行顺序（硬约束）：
1. Operator 派发 sub0（仅负责该模型）。
2. sub0 派发 sub1 执行 round1（按 EXEC）。
3. sub0 监督/质询 sub1，收集证据并完成 round1 评分。
4. round1 完成本轮并停止继续派发后，sub0 派发 sub2 执行 round2（按 EXEC）。
5. sub0 监督/质询 sub2，收集证据并完成 round2 评分。
6. sub0 输出该模型最终汇总报告。

禁止：
- 不得先跑 round2 再补 round1。
- 不得把 round1/round2 合并成单轮替代。

---

## 3) 模型一致性与重派规则（必须）

### 3.1 开场验模与异常分流
- sub1/sub2 在执行开头必须回显模型身份（`MODEL_ID_ECHO` / 事件流 `model_change.modelId`）。
- 验模用于发现“是否派错模型”，不因非实质性字符差异判定为不匹配。
- **若确认是错误模型族（Mismatch）：**
  1. **sub0 动作**：立即停止后续命令并等待指令，向 Operator 汇报归因（是 Operator 发错了，还是执行体产生运行时异常）。
  2. **Operator 裁决**：
     - 若 **Operator 错**（参数发错）：直接 Kill sub0，修正后重开新 sub0。（二级子代理重派次数 = 0）
     - 若 **Runtime 错**（偶发运行时异常）：下令 sub0 重派执行体。

### 3.2 二级子代理重派上限（仅限 Runtime 异常）
- 仅在 Operator 确认“参数无误、是执行端问题”并下令重派时，才启用此规则。
- **禁止 sub0 在未收到 Operator 明确 `Retry` 指令时自动重派。**
- 每个角色（sub1 或 sub2）最多重派 2 次。
- 超过上限仍失败：该轮判失败并完成本轮并停止继续派发，不伪造通过。

---

## 4) 项目默认约束（可由 Operator 覆盖）

- 单任务超时：15 分钟
- T4：`T4_REQUIRED=ON`（不可直接 SKIPPED）
- 模型匹配：采用标准化匹配（忽略大小写，允许 provider 前缀差异）
- 分支命名（固定模板）：`SELF_AUDIT_BRANCH=self-audit/<Run_ID>/round<round>`
- 提交命名（固定模板）：`self-audit(exec): <Run_ID> round<round> T3 artifact`

---

## 5) 多模型评测策略（必须串行）

若一次测多个模型，必须严格串行，并遵循以下规范：

### 5.1 批次命名与 Checklist（必须）
Operator 必须在启动前创建状态跟踪文件 `Audit-Report/<YYYY-MM-DD>/CHECKLIST_<Batch_ID>.md`。

**ID 命名规范**：
- **Batch ID**（大项目）：`BATCH_<YYYYMMDD>_<HHMM>_<Tag>`
- **Run ID**（单次执行）：`<Batch_ID>_M<Seq>`

#### 5.1.1 ID 强制生成规程（防幻觉协议）
**严禁凭逻辑推理生成时间戳。** Operator 在定义 `Batch_ID` 前，必须强制执行物理取时：
```bash
# 必须使用此命令的回显作为 ID 的时间部分
date +%Y%m%d_%H%M
```
若发现 ID 时间戳与 `ANCHOR_UTC` 物理时间偏差 > 10 分钟，该次评测视为 **逻辑溢出（Cognitive Drift）**，必须在 Checklist 中标注。

**Checklist 模板（Operator 独占维护）**：
```markdown
# CHECKLIST — <Batch_ID>

## 模型 1：<Target Model ID> (Run: <Run_ID>)
- [ ] sub0 启动 & 验模通过
- [ ] Round 1 (sub1) 完成
- [ ] Round 2 (sub2) 完成
- [ ] 本模型汇总报告完成

## 模型 2：<Target Model ID> (Run: <Run_ID>)
...
```

### 5.2 串行执行流
1. Operator 创建 Checklist。
2. 启动模型 1（M1）：`派 sub0 -> round1/round2 -> 完成本轮并停止继续派发` -> **Operator 打勾**。
3. 启动模型 2（M2）：`派 sub0 -> round1/round2 -> 完成本轮并停止继续派发` -> **Operator 打勾**。

禁止并发：
- 不得同时派多个 sub0 评不同模型。
- 必须“做一个、收一份证据、再开下一个”。

### 5.3 产物路径与命名规范（必须）
为确保审计链路可追溯，所有角色必须严格遵守以下路径规范：

1. **[sub1/sub2 职责]：执行报告**
   - 路径：`Audit-Report/<YYYY-MM-DD>/exec_<Run_ID>_round<1|2>.md`
   - 内容：原始执行证据。

2. **[sub0 职责]：评审报告（含轨道 1 评分）**
   - 路径：`Audit-Report/<YYYY-MM-DD>/review_<Run_ID>_round<1|2>.md`
   - 内容：质询记录、证据核验、轨道 1 分数。

3. **[Operator 职责]：批次总表与轨道 2 审计**
   - 路径：`Audit-Report/<YYYY-MM-DD>/CHECKLIST_<Batch_ID>.md`
   - 内容：整批模型进度跟踪、对 sub0 的轨道 2 最终审计结论。

---

## 6) 评分策略（Operator 规则）

每个模型至少输出：
1. round1 单独评分
2. round2 单独评分
3. 模型汇总评分（含风险与结论）

### 6.1 双轨审计职责（必须）
为确保评测公正性，采取“执行与编排分离”的审计模式：

1. **[sub0 职责]：打出“模型执行分”（轨道 1）**
   - sub0 负责评估执行体（sub1/sub2）的能力。
   - 必须严格对照 `SCORING-UNIVERSAL.md` **轨道 1** 标准，给出 D1-D5 原始分。

2. **[Operator 职责]：打出“编排质量分”（轨道 2）**
   - Operator 负责评估子代（sub0）的评审表现。
   - 必须严格对照 `SCORING-UNIVERSAL.md` **轨道 2** 标准，审计记录合规性、证据归档完整性及门控执行情况。
   - 轨道 2 的 PASS/FAIL 结论由 Operator 在验收 sub0 报告时最终判定。

评分原则：
- 不把编排失误（轨道 2 故障）直接扣到模型执行分（轨道 1）上。

---

## 7) Fail-Fast（Operator 裁决规则）

出现以下任一情况，可要求立即停止当前模型并纠偏：
- sub0 未按 `sub1(round1) -> sub2(round2)` 顺序执行
- **[时序熔断]** sub0 下发任务后，超过系统设定阈值（默认 15 分钟）未收到 sub1/sub2 的 CHECKPOINT 信号，陷入死锁。判定为调度失败，应 Kill 进程并重试或归因。
- 仅口头声称进入下一轮，但无工具事件证据
- 开场验模失败却未按规则重派/完成本轮并停止继续派发
- 多模型评测出现并发 sub0

---

## 8) 验模异常归因与记录（判责必填）

当出现模型回显异常、模型不一致或重派时，sub0 必须先向 Operator 即时回报，再进入后续动作；最终报告也必须包含归因标签（至少 1 个）：

- `FAULT_OPERATOR_INPUT`：Operator 下发模型目标/参数错误。
- `FAULT_SUB0_DISPATCH`：sub0 派发时模型参数传错、漏传或派发流程错误。
- `FAULT_EXEC_RUNTIME`：执行体运行时回显异常、执行偏差或环境导致异常。
- `FAULT_SPEC_AMBIGUITY`：文档规则歧义导致执行分歧。

记录格式建议：
- `Attribution: <TAG>`
- `Evidence: <关键证据（命令/回显/tool事件）>`
- `Action: <已采取补救动作>`

目的：让 Operator 能快速判定是“我说错了 / sub0 执行错了 / 需求没讲清楚”。

### 8.1 Operator 纠错动作（必须）
- 若归因为 `FAULT_OPERATOR_INPUT`：
  1) Operator 立刻修正派工参数/规则；
  2) 关闭当前在跑的 sub0 进程（避免沿用错误上下文继续执行）；
  3) 重新派发一个新的 sub0，从该模型评测起点重开。

---

## 9) 变更控制

- 先更新 `OPERATOR` 规则，再回写 `REVIEW`/`EXEC`。
- 未经 Operator 明确确认，不改核心拓扑、重派上限与评分规则。

---

## 10) 当前状态（迁移说明）

本文件是 Operator 决策最终依据。REVIEW/EXEC 需与本文件保持一致；若冲突，以本文件为准。
