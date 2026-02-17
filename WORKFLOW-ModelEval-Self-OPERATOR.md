# WORKFLOW — ModelEval-Self（OPERATOR / 主会话决策层）

> Version: `operator-v1.0`
> Last Updated: `2026-02-17`
> Status: `active`

> 适用对象：Operator（你）+ 主会话助手（我）
>
> 目的：只定义“评测目标、约束、决策与验收口径”，不承载执行细节。
>
> 执行细节请看：
> - REVIEW：`WORKFLOW-ModelEval-Self-REVIEW.md`（给 sub1 编排/评审）
> - EXEC：`WORKFLOW-ModelEval-Self-EXEC.md`（给孙代执行）

---

## 1) 本层职责（Operator 层）

1. 定义本次评测目标（模型、样本、重试上限、超时）。
2. 决定评分口径（执行优先 / 严格门控 / 双轨并行）。
3. 审批关键策略变化（如 T4_REQUIRED、模型匹配规则）。
4. 对最终结果做裁决（继续下一模型 / 重跑 / 终止）。

> 本层不直接写执行证据，不替代 REVIEW/EXEC 跑任务。

---

## 2) 本次项目默认约束（可由 Operator 覆盖）

- 模型集合：
  - `longcat/LongCat-Flash-Chat`
  - `longcat/LongCat-Flash-Lite`
  - `longcat/LongCat-Flash-Thinking-2601`
- 调度方式：串行（模型串行；每模型内部样本串行）
- 单任务超时：15 分钟
- T4：`T4_REQUIRED=ON`（不可直接 SKIPPED）

---

## 3) 任务结构（Operator 口径）

> 该结构由 Operator 定义，REVIEW 必须执行，不得降级。

- 单模型采用**单轮任务**（不再拆 round1/round2 双轮）。
- 每次任务失败时，可重试；默认上限：**最多 2 次重试**。
- 即每模型最多 3 次尝试：`Attempt-1（首次） -> Retry-1 -> Retry-2`。
- 仅当 `HARD_ABORT` 时可提前停止后续重试。

---

## 4) 模型一致性策略（Operator 决策位）

### 4.1 强制项
- spawn 孙代时必须显式传参 `model=<target>`。
- 孙代开场先回显 `MODEL_ID_ECHO`（事件流头部 `model_change.modelId`）。

### 4.2 匹配口径（建议）
- 使用“标准化匹配”（忽略大小写、允许 provider 前缀差异）。
- 仅在标准化后仍不匹配时，判 `MODEL_MISMATCH`。

### 4.3 失败处理
- 首次 mismatch：允许进入 `Retry-1`。
- `Retry-1` 仍 mismatch：允许进入 `Retry-2`（最后一次）。
- `Retry-2` 仍 mismatch：该模型样本判失败，但不伪造通过。

---

## 5) 评分策略（Operator 选项）

为避免“编排失误污染模型分”，采用双轨：

1) **模型执行分**（Executor 能力）
- 仅看 T1-T4、真实性、超时、证据质量。

2) **编排流程分**（Reviewer/Sub1 质量）
- 看门控是否完整、是否按结构派发、是否漏启动重试。

> 默认：先给模型执行分；流程问题单列告警，不直接扣模型能力分。

---

## 6) 必要验收输出（Operator 读）

每个模型至少应有：
1. 尝试摘要（Attempt-1 / Retry-1 / Retry-2 分开）
2. 评分块（每次尝试单独分）
3. 汇总结论（模型执行分 + 编排流程告警）
4. 下一步建议（继续/重跑/终止）

---

## 7) Fail-Fast（Operator 裁决规则）

出现以下任一情况，可直接要求停止当前模型并纠偏：
- 未按结构执行（例如应重试但未 spawn，或超出重试上限）
- 仅口头宣称进入下一尝试，但无工具事件证据
- 擅自把“单轮+重试”改成其他结构且未经 Operator 许可
- 模型不一致且无重试/无解释

---

## 8) 变更控制

- 先更新 `OPERATOR` 口径，再回写到 `REVIEW`。
- 未经 Operator 确认，不修改评分阈值与核心门控结构。

---

## 9) 当前状态（迁移说明）

本文件为从 `WORKFLOW-ModelEval-Self-REVIEW.md` 中先行摘出的 Operator 层内容。
待你确认后，再从 REVIEW 删除对应章节，完成职责分离。
