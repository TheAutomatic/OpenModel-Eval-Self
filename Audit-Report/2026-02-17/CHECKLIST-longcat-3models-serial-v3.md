# CHECKLIST — LongCat 三模型串行评测大项目（v3）

- 项目启动时间（Asia/Shanghai）：**2026-02-17 08:40**
- 执行模式：主会话发起 → 每轮 1 个 subagent → 该 subagent 串行派发 2 个孙代（A→B）
- 单任务超时：**15 分钟**
- 门控规则：当前项未收口，禁止进入下一项
- T4 规则：**必须执行（T4_REQUIRED=ON）**；仅在环境客观不支持时允许 `T4=BLOCKED`（必须附阻断证据），禁止直接 `T4=SKIPPED`
- 模型锁定门控（新增）：
  - 每次派孙代必须显式传参：`model=longcat/...`（缺失即禁止启动）
  - 孙代开场必须回显 `model_change.modelId`；若不等于目标模型，立即判 `MODEL_MISMATCH` 并重派

---

## 模型 1（纠偏重跑）：longcat/LongCat-Flash-Chat
- [~] 本模型执行中（v3重跑启动：2026-02-17 08:51 Asia/Shanghai，sub=agent:main:subagent:efab3aa7-f26f-408f-8c7f-031dc6bcf73f）
- [ ] 孙代 A 评测完成（≤15m）
- [ ] 子轮 A 结果验收完成
- [ ] 孙代 B 评测完成（≤15m）
- [ ] 子轮 B 结果验收完成
- [ ] 本模型汇总报告完成（含 T4 执行证据）

## 模型 2：longcat/LongCat-Flash-Lite
- [ ] 孙代 A 评测完成（≤15m）
- [ ] 子轮 A 结果验收完成
- [ ] 孙代 B 评测完成（≤15m）
- [ ] 子轮 B 结果验收完成
- [ ] 本模型汇总报告完成（含 T4 执行证据）

## 模型 3：longcat/LongCat-Flash-Thinking-2601
- [ ] 孙代 A 评测完成（≤15m）
- [ ] 子轮 A 结果验收完成
- [ ] 孙代 B 评测完成（≤15m）
- [ ] 子轮 B 结果验收完成
- [ ] 本模型汇总报告完成（含 T4 执行证据）

---

## 最终收口
- [ ] 三模型横向对比总报告完成
- [ ] 明确结论（稳定性/真实性/完成度/超时情况）
- [ ] 可复核证据路径整理完成
