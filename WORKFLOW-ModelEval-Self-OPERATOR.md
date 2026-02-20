# WORKFLOW — ModelEval-Self（OPERATOR / 主控台编排者手册）

> Version: `1.6.1`
> Last Updated: `2026-02-20`
> Status: `active`

> **Role**：SG_OPERATOR（主控台 / 决策层）
>
> ```yaml
> EVAL_MODE: ORCHESTRATION_CONTROL
> ```

---

## 1) 职责边界（Operator 层）

1. 选择评测目标（单模型 / 多模型串行）。
2. 派发 `sub0`，并维持生命周期控制（挂起、放行、熔断）。
3. 对 `sub0` 交付执行轨道 2 审计与最终裁决。

**边界规则（硬约束）**：
- Operator 不替代 `sub0/sub1/sub2` 运行执行命令。
- 执行细节真相源：
  - REVIEW：`WORKFLOW-ModelEval-Self-REVIEW.md`
  - EXEC：`WORKFLOW-ModelEval-Self-EXEC.md`

---

## 2) 标准拓扑与顺序硬约束

固定控制流：`OPERATOR(Main) -> sub0(Reviewer) -> sub1(R1) -> sub2(R2)`

**顺序硬约束**：
- 禁止 `Round2` 先于 `Round1`。
- 禁止单轮替代双轮（不得把 R1/R2 合并为一次测试）。

---

## 3) 启动注入与环境锚定（Context Injection）

派发 `sub0` 前必须完成：

1. **Run_ID（UTC）**：`date -u +"%Y%m%d_%H%M"`
2. **Truth Gate 注入**：在给 `sub0` 的初始指令中明确：
   - R1=原生基线
   - R2=干预测试
   - 派发 `sub2` 时必须强制先读 `WORKFLOW-Truth-Gate.md` 并输出 `[TRUTH_GATE_ACK]`
3. **分支拓扑**：`self-audit/<Run_ID>/round<round>`
4. **参数齐备**：`Run_ID`, `TARGET_MODEL`, `SELF_AUDIT_BRANCH`, REVIEW 路径

---

## 4) 模型一致性与重派规则

### 4.1 开场验模与异常分流
- `sub1/sub2` 必须回显模型身份（用于核验是否派错模型）。
- 若判定为 `MODEL_ECHO_MISMATCH`：
  - `sub0` 必须暂停推进并上报归因。
  - Operator 裁决：
    - `FAULT_OPERATOR_INPUT`：修正参数后重开 `sub0`
    - `FAULT_EXEC_RUNTIME`：允许重派执行体

### 4.2 重派上限（仅 Runtime 异常）
- 未收到 Operator 明确 `Retry` 指令，`sub0` 禁止自动重派。
- 每个角色（sub1/sub2）重派上限：2 次。
- 超过上限仍失败：该轮失败并收口，不得伪造通过。

---

## 5) 生命周期控制与 Fail-Fast

### 5.1 阻塞等待协议
- 派发 `sub0` 后，Operator 进入 `SUSPEND_WAITING`。
- 仅当收到 `ROUND1_CLOSED` / `ROUND2_CLOSED` 且产物落盘，才允许状态推进。

### 5.2 Fail-Fast 条件（命中即熔断）
- 超时：超过 15 分钟无 checkpoint ACK。
- 时序倒置：R1 未闭环即请求进入 R2。
- 无证推进：仅文本声称“完成/进入下一轮”，无工具证据链。
- 归档死循环：重复抓错时间窗会话。
- 多模型模式下并发多个 `sub0`。

---

## 6) 多模型批次策略（必须串行）

多模型评测必须串行：**一个模型闭环后，才能推进下一个模型**。

### 6.1 批次命名与清单
- 批次文件：`Audit-Report/<YYYY-MM-DD>/CHECKLIST_<Batch_ID>.md`
- 命名：
  - `Batch_ID=BATCH_<YYYYMMDD>_<HHMM>_<Tag>`
  - `Run_ID=<Batch_ID>_M<Seq>`

**取时要求（防幻觉）**：
- 生成 `Batch_ID` 前必须执行物理时间命令，不得脑补时间戳。

**Checklist 模板（最小）**：
```markdown
# CHECKLIST — <Batch_ID>

## 模型 <N>: <Target Model> (Run: <Run_ID>)
- [ ] sub0 启动 & 验模通过
- [ ] Round1 完成
- [ ] Round2 完成
- [ ] review_round1/review_round2 已落盘
- [ ] 轨道2盖章 + Delta Analysis 完成
- [ ] closure gate PASS
```

### 6.2 串行推进规则
- 禁止并发多个 sub0。
- 必须“完成一个模型的收尾清单，再启动下一个模型”。

---

## 7) 轨道 2 验收与结论

### 7.1 轨道 2 审计项
- 流程完整性（Challenge 是否闭环）
- 证据归档（raw_logs/transcript/receipt/manifest）
- 记录合规性（Git 记录有效）

### 7.2 Operator 覆写区块（必须填写）
```markdown
### 轨道 2：编排质量评定 (Orchestration Audit) - [Operator 专用]
- 流程完整性: <PASS / FAIL>
- 证据归档: <PASS / FAIL / INCOMPLETE>
- 记录合规性: <PASS / FAIL>
- 编排结论: <正常 / 存在疏漏 / 执行失控>
```

### 7.3 Delta Analysis（R1 vs R2）
`review_<Run_ID>_round2.md` 末尾必须追加：
- `Native-Good`
- `Prompt-Steerable`
- `Hopeless`
- `UNDECIDED / INVALID_COMPARISON`

---

## 8) 异常归因与判责记录（必填）

当出现错配/重派/中断，报告必须包含：
- `Attribution`: `FAULT_OPERATOR_INPUT | FAULT_SUB0_DISPATCH | FAULT_EXEC_RUNTIME | FAULT_SPEC_AMBIGUITY`
- `Evidence`: 关键命令/回执/日志证据
- `Action`: 已执行纠偏动作

---

## 9) Operator Fuse Checklist（终局前）

- [ ] Run_ID/目标模型/分支参数已无歧义派发给 sub0。
- [ ] 已完成阻塞等待控制，无越序推进。
- [ ] `raw_logs` 存在且非空。
- [ ] `receipts/exec_checkpoint_<Run_ID>_round*.jsonl` 存在，checkpoint 闭环 COMPLETE。
- [ ] Challenge Structured Record（Q1~Q4 四字段）完整，challenge 闭环 COMPLETE。
- [ ] `manifest_<Run_ID>_round*.sha256` 已生成（至少 round1+round2）。
- [ ] D4 自动校验摘要存在（`CHALLENGE_COMPLETE` / `D4_FORCED_TO_ZERO`）。
- [ ] 轨道 2 区块已覆写（无占位符残留）。
- [ ] `Delta Analysis` 已追加到 round2。
- [ ] 已执行 `scripts/operator_closure_gate.sh <Run_ID> <YYYY-MM-DD>` 且返回 `[GATE] PASS`。
