# Claude 评审指南（OpenModel-Eval-Self）

> 目的：让 Claude 能快速、稳定地读懂一次自评估，并给出可执行的改进意见（不是泛泛而谈）。

## 1) 先读什么（固定顺序）
1. `README.md`（了解目录与产物约定）
2. `WORKFLOW-OpenClaw-SelfAudit-REVIEW.md`（判分规则与硬约束）
3. `WORKFLOW-OpenClaw-SelfAudit-EXEC.md`（执行流程与证据格式）
4. 目标 run 的 4 份报告：
   - `Audit-Report/<date>/exec_openclaw_run<run_id>_round1.md`
   - `Audit-Report/<date>/exec_openclaw_run<run_id>_round2.md`
   - `Audit-Report/<date>/review_openclaw_run<run_id>_round1.md`
   - `Audit-Report/<date>/review_openclaw_run<run_id>_round2.md`

## 2) Claude 应该检查什么

### A. 规则一致性（先看 REVIEW）
- REVIEW 的结论是否与手册规则一致：
  - 是否明确 `Result` 与 `Audit Completeness`
  - 是否抽查了至少 2 个 session
  - 是否覆盖 T3（git commit/push）
  - 若缺证据，是否标记 `INCOMPLETE` 或 `Fail`

### B. 证据闭环（再看 EXEC + _sessions）
- EXEC 报告中的关键声明是否能在 `_sessions/*.gz` 里对上：
  - T1/T2/T3/T4 是否都存在真实工具事件痕迹
  - T3 是否能命中 `git commit` 与 `git push`
  - 有没有“报告写了输出，但事件流没有 toolCall/toolResult”的伪造风险

### C. KR 节奏符合性
- 是否有 `CHECKPOINT` + `CHECKPOINT_ID`
- 是否严格使用 `WAITING_REVIEW_OK_NEXT <CHECKPOINT_ID>` 与 `OK_NEXT <CHECKPOINT_ID>` 配对放行
- 是否体现“逐点闭环”（不是先全跑完再统一复盘）
- 是否将无关 inter-session 文本（announce/ping）视为 `CONTROL_MESSAGE_IGNORED`，不改变执行状态

## 3) 给意见的格式（必须可执行）
请按这三档输出，不要混在一段里：

1. **MUST FIX（必须修）**
   - 会导致误判、假阳性/假阴性、或破坏审计可复现性的点。
   - 每条要包含：问题 → 风险 → 最小修改建议（改哪一段）。

2. **SHOULD IMPROVE（建议优化）**
   - 不改也能跑，但会降低效率/可读性/稳定性。
   - 每条给出“改前/改后”的简短示例。

3. **NIT（可选润色）**
   - 命名、措辞、模板细节、重复段落清理。

## 4) Claude 输出模板（建议直接复用）
```markdown
## 结论
- 该 runbook/该次 run 的总体判断：<可用/部分可用/不可用>

## MUST FIX
1) <标题>
- 问题：
- 风险：
- 最小修改：

## SHOULD IMPROVE
1) <标题>
- 现状：
- 建议：

## NIT
- ...

## 可直接落盘的 patch 建议
- 文件：<path>
- 替换：<old text>
- 新文案：<new text>
```

## 5) 评审边界（避免跑偏）
- 不讨论与本仓库无关的系统哲学或大改架构。
- 不要求改历史提交（除非明确发生泄露/严重错误）。
- 只围绕“证据是否可复核、规则是否可执行、结论是否可重现”给意见。
