# 独立审稿人B意见书（可审计性 / 防伪造 / 状态机鲁棒性）

- 日期：2026-02-20（Asia/Shanghai）
- 审查对象：`CLAUDE-REVIEW-GUIDE-UNIFIED.md`（v1.2.3）及本次 run `20260219_1802` 的已落盘证据链
- 关注维度：可审计性、防伪造、状态机鲁棒性

## 结论等级

**PARTIAL**

理由：
1. 任务主流程（T1~T4、R1/R2、Git 证据）基本跑通。  
2. 但关键“防伪造控制点”未形成**可机器复核的闭环证据**：尤其是 checkpoint 握手与 R1 challenge 闭环。  
3. 状态机存在“文本协议与工具能力不一致”的结构性缺陷（规范要求 `sessions_send`，实际运行环境不可用/未落证），导致规则可写但不可证。

---

## 风险矩阵（问题 -> 风险 -> 影响）

| 问题 | 风险 | 影响 |
|---|---|---|
| 1) Checkpoint 仅文本出现，缺 tool-level 回执链 | 可伪造“我已等待/已放行” | 无法证明顺序执行，审计可被绕过 |
| 2) `sessions_send` 作为强制动作，但运行面不保证可用 | 规范-实现断裂 | 执行者可用 `NON-EVIDENCE` 规避关键控制 |
| 3) R1 Challenge Q2~Q4未稳定闭环（历史已出现） | D4 可被主观打分 | “抗质询能力”维度不可复核 |
| 4) R1->R2 Gate 当前以“文件存在”作为主要条件 | 低门槛放行 | 带缺陷证据进入 R2，污染整轮结论 |
| 5) 归档候选依赖时间窗 + 本地时区解析 | 漏抓/错抓会话 | 可能抽错母带，产生假阴性/假阳性 |
| 6) 会话人工补拣（按 UUID 手工拷贝）缺防篡改元数据 | 可选择性取证 | 审计复盘不具可重复性 |
| 7) transcript 与 raw 没有强绑定 hash 清单 | 事后替换难发现 | 证据完整性不可验证 |
| 8) 状态机缺“异常分支统一终态码” | 异常处理漂移 | 同类故障在不同 run 口径不一致 |
| 9) Operator/Reviewer可多次 steer 已结束子会话 | 状态污染 | 审计事件序列出现歧义 |
| 10) 评分与证据映射未强制自动校验 | 评分可被文本主导 | D1~D5 可信度下降 |

---

## 修改建议（可落地，含优先级）

### P0（立即）
1. **引入“握手收据”强制产物（JSON）**  
   - 每个 checkpoint 生成 `checkpoint_receipt_<run>_<round>.jsonl`，字段至少含：`checkpoint_id / sender_session / receiver_session / sent_ts / ack_ts / ack_payload / raw_event_ref`。  
   - 无收据则该 Task 不得记为完成。

2. **把 `sessions_send` 从“文本要求”改为“能力探测+降级策略”**  
   - STATE0 增加 `CAPABILITY_CHECK`：检测是否可用跨会话发送工具。  
   - 若不可用，立即切换到明确定义的替代通道（如 `subagents steer` + receipt）并写入 `mode=degraded`。

3. **R1->R2 Gate 改为三条件硬门**  
   - `gate_pass = review_round1_exists && raw_logs_count>=N && challenge_closure==true`。  
   - 任一不满足：`ROUND_GATE_DENIED`，禁止进入 R2。

4. **Challenge 闭环结构化**  
   - 固定输出 `challenge_round1_<run>.json`，强制字段：`Q1..Q4 ask/answer/evidence_refs/verdict`。  
   - 缺任一字段则 D4 自动封顶（例如 <=8）。

### P1（本周）
5. **归档改为“双锚点+哈希清单”**  
   - 使用 `ANCHOR_UTC` 与 `MARKER_UTC` 双窗筛选；并产出 `manifest.sha256`（raw/transcript/review 全量哈希）。

6. **引入“会话选择器脚本”替代人工拷贝**  
   - 脚本输入 run_id + round + 时间锚，输出稳定候选集合与原因（mtime/消息命中）。

7. **状态机增加统一终态码**  
   - 如 `COMPLETE / INCOMPLETE / FAIL_FAST / GATE_DENIED / EVIDENCE_MISSING`，便于跨 run 横向比较。

8. **评分自动校验器**  
   - 对 D1~D5 与证据引用数量做静态检查；不满足则阻止写入最终 rating。

### P2（迭代）
9. **反伪造增强：事件链签名**  
   - 对关键事件（checkpoint/challenge/gate）计算链式摘要（prev_hash + event_json）。

10. **Operator 干预审计日志化**  
   - 所有 steer/kill/retry 自动写 `operator_actions_<run>.jsonl`，避免口头叙述替代证据。

11. **跨 run UUID 冲突自动告警**  
   - 每次归档时扫描历史索引，命中共享会话则强制标 `SHARED_SESSION` 并降级结论。

12. **时区安全防护**  
   - 全流程统一 UTC 解析，禁止依赖本地默认时区；脚本启动先打印 `date -u` 与 parser 结果。

---

## 专项硬化方案

### A) Checkpoint 握手硬化
- **现状漏洞**：文本 `WAITING_REVIEW_OK_NEXT` 可出现，但无可验证 ACK 链。  
- **方案**：
  1. 定义消息规范：`WAITING <checkpoint_id> <nonce>` / `OK_NEXT <checkpoint_id> <nonce>`。  
  2. 发送端与接收端各自产生 receipt（双边回执）。  
  3. 审计侧只认“nonce 一致 + 双边时间有序 + raw_event_ref 存在”。

### B) Challenge 闭环硬化
- **现状漏洞**：Q2~Q4 易因会话结束/通道问题变 `NON-EVIDENCE`，但流程仍可前进。  
- **方案**：
  1. Challenge 改为“同步窗口任务”：若执行者不可交互，立即标记 `challenge_unavailable` 并触发补救分支。  
  2. Q4 必须引用 T2 的具体字节/字符核验命令输出；无命令输出则 Q4=无效。  
  3. D4 评分由脚本按闭环状态自动计算，人工只能在限定区间微调。

### C) R1->R2 Gate 硬化
- **现状漏洞**：以“文件已写”代替“控制点已闭环”。  
- **方案**：
  1. 生成 `gate_r1_to_r2.json`，字段含：`raw_count/challenge_closure/checkpoint_closure/model_match/rating_check`。  
  2. 仅当全部 `true` 才允许 spawn sub2。  
  3. Gate 文件必须进入 hash manifest 并在 review 中引用。

---

## “无需全量重跑”的修复路线图

### 阶段0（当天，可立即）
- 对现有 `raw_logs` 做离线重建：补出 `checkpoint_receipt` 与 `challenge_closure` 判定文件（基于已有 jsonl）。
- 产出 `manifest.sha256` 绑定当前证据集，冻结本次 run 的审计基线。

### 阶段1（1天）
- 仅改 runbook + 脚本（不重跑 T1~T4）：
  - 加入 capability check、gate 三条件、challenge JSON 模板、统一终态码。

### 阶段2（半天）
- 做**最小补跑**（非全量）：
  - 只重放 R1 Challenge 闭环与 checkpoint 协议验证（不重做业务任务）。
  - 目标是验证“协议可证”而非“任务再执行”。

### 阶段3（后续）
- 将校验器接入每轮结束钩子，未过门禁不得写最终 `PASS`。

---

## 最终意见

本指南方向正确（强调全量事件流与防伪造），但本次 run 暴露出**规范-实现耦合不足**：关键控制点未被工具级证据封闭。建议按上述 P0/P1 先完成“可证明的状态机闭环”，再谈评分稳定性；这样可以在**不全量重跑**的前提下，把当前结果从“可参考”提升到“可审计复现”。
