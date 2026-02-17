# WORKFLOW — ModelEval-Self（OPERATOR / 主会话决策层）

> Version: `1.0`
> Last Updated: `2026-02-17`
> Status: `active`

> 适用对象：Operator（你）+ 主会话助手（我）
>
> 目的：只定义“评测目标、约束、决策与验收口径”，不承载执行细节。
>
> 执行细节请看：
> - REVIEW：`WORKFLOW-ModelEval-Self-REVIEW.md`（给 sub0 编排/评审）
> - EXEC：`WORKFLOW-ModelEval-Self-EXEC.md`（给孙代执行）

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
4. round1 收口后，sub0 派发 sub2 执行 round2（按 EXEC）。
5. sub0 监督/质询 sub2，收集证据并完成 round2 评分。
6. sub0 输出该模型最终汇总报告。

禁止：
- 不得先跑 round2 再补 round1。
- 不得把 round1/round2 合并成单轮替代。

---

## 3) 模型一致性与重派规则（必须）

### 3.1 开场验模
- sub1/sub2 在执行开头必须回显模型身份（`MODEL_ID_ECHO` / 事件流 `model_change.modelId`）。
- 若开场即模型不一致：立即停止该次执行，进入重派。

### 3.2 重派上限
- 开场验模失败时，允许重派同角色执行体。
- 每个角色（sub1 或 sub2）最多重派 2 次。
- 超过上限仍失败：该轮判失败并收口，不伪造通过。

---

## 4) 项目默认约束（可由 Operator 覆盖）

- 单任务超时：15 分钟
- T4：`T4_REQUIRED=ON`（不可直接 SKIPPED）
- 模型匹配：采用标准化匹配（忽略大小写，允许 provider 前缀差异）

---

## 5) 多模型评测策略（必须串行）

若一次测多个模型，必须严格串行：
1. 先完成模型1：`派 sub0.1 -> round1/round2 -> 收口报告`
2. 再启动模型2：`派 sub0.2 -> round1/round2 -> 收口报告`
3. 再启动模型3：`派 sub0.3 -> round1/round2 -> 收口报告`

禁止并发：
- 不得同时派多个 sub0 评不同模型。
- 必须“做一个、收一份证据、再开下一个”。

---

## 6) 评分策略（Operator 口径）

每个模型至少输出：
1. round1 单独评分
2. round2 单独评分
3. 模型汇总评分（含风险与结论）

评分原则：
- 模型执行分（看 executor 执行质量）
- 编排流程分（看 sub0 门控与取证质量）
- 不把编排失误直接扣到模型执行分上

---

## 7) Fail-Fast（Operator 裁决规则）

出现以下任一情况，可要求立即停止当前模型并纠偏：
- sub0 未按 `sub1(round1) -> sub2(round2)` 顺序执行
- 仅口头声称进入下一轮，但无工具事件证据
- 开场验模失败却未按规则重派/收口
- 多模型评测出现并发 sub0

---

## 8) 变更控制

- 先更新 `OPERATOR` 口径，再回写 `REVIEW`/`EXEC`。
- 未经 Operator 明确确认，不改核心拓扑、重派上限与评分口径。

---

## 9) 当前状态（迁移说明）

本文件是 Operator 决策真相源。REVIEW/EXEC 需与本文件保持一致；若冲突，以本文件为准。
