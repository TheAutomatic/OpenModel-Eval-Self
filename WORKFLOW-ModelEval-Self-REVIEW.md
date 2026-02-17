# WORKFLOW — ModelEval-Self（REVIEW / sub1 编排与评审手册）

> Version: `review-v2.0-operator-aligned`
> Last Updated: `2026-02-17`
> Status: `active`
> Audience: `sub1 (reviewer/orchestrator)`

---

## 0) 边界与输入

### 0.1 你是谁（sub1）
你是评审编排器（reviewer/orchestrator），职责是：
1. 串行派发执行样本（孙代执行体）。
2. 做模型一致性核验与执行证据核验。
3. 输出评分与裁决报告。

你**不负责**：
- 替执行体代跑 T1/T2/T3/T4。
- 替 Operator 改目标、改评分口径、改重试上限。

### 0.2 你必须遵循
- `WORKFLOW-ModelEval-Self-OPERATOR.md`（策略真相源）
- `WORKFLOW-ModelEval-Self-EXEC.md`（执行体动作规范）
- `SCORING-UNIVERSAL.md`
- `SCORING-MAPPING.md`

若 REVIEW 与 OPERATOR 冲突：**以 OPERATOR 为准**。

---

## 1) 任务结构（给 sub1 的执行结构）

按单模型执行，最多 3 次尝试：
- Attempt-1（首次）
- Retry-1（可选）
- Retry-2（可选，最后一次）

触发规则：
- Attempt-1 成功：直接收口，不进入重试。
- Attempt-1 失败：进入 Retry-1。
- Retry-1 失败：进入 Retry-2。
- Retry-2 失败：该模型收口为 Fail。
- 出现 `HARD_ABORT`：立即停止本模型后续尝试。

---

## 2) 每次尝试的硬门控

### 2.1 派发前
必须显式传参：
- `model=<target model>`
- `runTimeoutSeconds=900`（默认 15 分钟）

### 2.2 派发后（先验模，后执行）
每次尝试都必须先完成：
1. 执行体回显 `MODEL_ID_ECHO`（来源于事件流头部 `model_change.modelId`）。
2. 按标准化匹配规则判定是否匹配目标模型（忽略大小写、允许 provider 前缀差异）。

- 匹配：允许进入 T1-T4 评测。
- 不匹配：标记 `MODEL_MISMATCH`，该尝试判失败，按重试规则推进。

> 禁止“先跑完整 T1-T4，最后才验模”的延后验模。

### 2.3 完成判定
每次尝试完成后，sub1 必须给出：
- T1/T2/T3/T4 状态（Pass/Partial/Fail/BLOCKED）
- Timeout（HIT/NO）
- 模型一致性判定（MATCH/MISMATCH）
- 关键证据摘要（命令/输出/rc）

---

## 3) 证据要求（REVIEW 验收）

### 3.1 必须有的证据
1. `sessions_spawn` 工具事件（每次尝试都要有）。
2. 执行体 toolCall/toolResult 链路（至少覆盖 T1/T2/T3/T4）。
3. 模型核验依据（`model_change.modelId` 来源）。
4. T3 git 证据（commit/push 输出或失败返回码）。
5. T4 证据（RUN 或 BLOCKED，禁止 SKIPPED）。

### 3.2 直接判失败的情况
- 口头声称已启动下一尝试，但无 `sessions_spawn` 证据。
- 声称执行命令，但事件流无对应 toolCall/toolResult。
- T4 标记为 SKIPPED（在 `T4_REQUIRED=ON` 前提下）。

---

## 4) 评分输出（sub1 产物）

每个模型必须输出两层评分：

1) **模型执行分**（Executor）
- 对 Attempt-1 / Retry-1 / Retry-2 分别打分（未发生的尝试写 N/A）。
- 维度：D1-D5，Total，Rating。

2) **编排流程分**（sub1）
- 仅评估 sub1 编排质量：门控、重试推进、证据完整性、是否漏启动。
- 不得把编排失误直接扣到模型执行分上。

---

## 5) 报告命名与落盘

建议命名：
- `review_<model_slug>_attempt1.md`
- `review_<model_slug>_retry1.md`
- `review_<model_slug>_retry2.md`
- `review_<model_slug>_final.md`

落盘目录：
- `Audit-Report/<YYYY-MM-DD>/`

---

## 6) 最终收口模板（每个模型）

```markdown
## Final Verdict (Reviewer)
- Model: <target>
- Attempts run: <1|2|3>
- Attempt results:
  - Attempt-1: <PASS/FAIL + reason>
  - Retry-1: <PASS/FAIL/N/A>
  - Retry-2: <PASS/FAIL/N/A>
- Model consistency: <MATCHED | MISMATCHED | PARTIAL>
- Model execution score: <Total + Rating>
- Orchestration score (sub1): <Total + Rating>
- Risks:
  - <risk 1>
  - <risk 2>
- Recommendation: <continue next model | rerun | stop>
```

---

## 7) REVIEW Fuse Checklist（提交前必勾）

- [ ] 我已读取 OPERATOR 并确认本次目标/模型/超时/重试上限。
- [ ] 每次尝试都显式传了 `model` 参数。
- [ ] 每次尝试都先完成 MODEL_ID_ECHO 验模，再进入执行。
- [ ] 所有尝试均有 `sessions_spawn` 证据；无口头推进。
- [ ] T4 在 `T4_REQUIRED=ON` 下未出现 SKIPPED。
- [ ] 已分别给出“模型执行分”和“编排流程分”。
- [ ] 已输出 final 收口结论与下一步建议。
