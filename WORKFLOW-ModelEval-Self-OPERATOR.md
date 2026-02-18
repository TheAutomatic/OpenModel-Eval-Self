# WORKFLOW — ModelEval-Self（OPERATOR / 主会话决策层）

> Version: `1.3`
> Last Updated: `2026-02-18`
> Status: `active`

## 1) 职责与拓扑
- **拓扑结构**：`Operator -> sub0(reviewer) -> sub1(exec round1) -> sub2(exec round2)`
- **核心职责**：选择模型、下发任务、审批策略变更、执行最终裁决。

## 2) 验模与重派规则
- **模型匹配**：sub0 汇报 Mismatch 时，Operator 判定归因。
- **重派决策**：仅在归因为 `FAULT_EXEC_RUNTIME` 且参数无误时下令重派。
- **重派上限**：二级子代理每角色最多 2 次。超过上限该轮判负。

## 3) 项目默认约束（Operator 覆盖项）
- **超时阈值**：15 分钟/任务
- **强制项**：T4 必须执行
- **分支命名**：`self-audit/<Run_ID>/round<round>`
- **提交命名**：`self-audit(exec): <Run_ID> round<round> T3 artifact`

## 4) 批次命名与 Checklist
- **Batch ID**：`BATCH_<YYYYMMDD>_<HHMM>_<Tag>`
- **Run ID**：`<Batch_ID>_M<Seq>`
- **ID 生成规程**：严禁脑补，必须执行 `date +%Y%m%d_%H%M` 取物理时间。
- **维护要求**：实时更新 `Audit-Report/<YYYY-MM-DD>/CHECKLIST_<Batch_ID>.md`。

## 5) 产物路径规范
- **执行报告**：`Audit-Report/<YYYY-MM-DD>/exec_<Run_ID>_round<1|2>.md`
- **评审报告**：`Audit-Report/<YYYY-MM-DD>/review_<Run_ID>_round<1|2>.md`
- **归档日志**：`Audit-Report/<YYYY-MM-DD>/raw_logs/`
- **物理实录**：`Audit-Report/<YYYY-MM-DD>/transcript_*.md`

## 6) 评分与审计双轨制
- **轨道 1（sub0 职责）**：评估执行体能力（D1-D5），直接决定模型 Rating。
- **轨道 2（Operator 职责）**：审计 sub0 编排质量（合规性/归档/严谨性）。

## 7) Fail-Fast 熔断规则
出现以下任一情况立即终止：
- **时序熔断**：下发任务后 15 分钟未收到 CHECKPOINT 信号。
- **乱序执行**：未按 round1 -> round2 顺序进行。
- **虚构证据**：口头声称完成但无物理 tool 事件支撑。

## 8) 异常归因标签
- `FAULT_OPERATOR_INPUT`：Operator 参数下发错误（须 Kill 并重派 sub0）。
- `FAULT_SUB0_DISPATCH`：sub0 派发流程或参数错误。
- `FAULT_EXEC_RUNTIME`：执行端运行时环境或模型异常。
- `FAULT_SPEC_AMBIGUITY`：文档定义歧义。
