# CHECKLIST — OPERATOR 瘦身（仅压缩，不改规则）

> 目标：仅做文案压缩与结构整理，保持全部规则与硬闸门语义不变。
> 适用文件：`WORKFLOW-ModelEval-Self-OPERATOR.md`

---

## A. 硬锁区（绝对不动）

- [ ] 不改任何判定条件（PASS/FAIL/INCOMPLETE 语义不变）
- [ ] 不删占位符拦截检查：
  - `grep -RInE "<PASS/FAIL|OPERATOR_OVERRIDE_BLOCK_START" Audit-Report/<YYYY-MM-DD>/review_<Run_ID>_round*.md`
- [ ] 不删收尾闸门脚本检查：
  - `scripts/operator_closure_gate.sh <Run_ID> <YYYY-MM-DD>` 且 `[GATE] PASS`
- [ ] 不删以下检查项：
  - `receipts/exec_checkpoint_<Run_ID>_round*.jsonl`
  - `Challenge Structured Record`
  - `manifest_<Run_ID>_round*.sha256`
  - `D4 自动校验摘要`
- [ ] 不改 Delta 四分类定义：
  - `Native-Good / Prompt-Steerable / Hopeless / UNDECIDED|INVALID_COMPARISON`
- [ ] 不改重派规则：
  - `sub0` 未获 `Retry` 禁止自动重派
  - `sub1/sub2` 重派上限 = 2

---

## B. 允许瘦身（可删可并）

- [ ] 删除重复解释句（同义保留一处）
- [ ] 合并重复“流程提醒”到单一章节
- [ ] 长句改短句，不改约束词（必须/禁止/仅当）
- [ ] 删除背景叙述，只留动作指令
- [ ] 统一章节编号与标题风格

---

## C. 章节级瘦身动作

### 1) 架构拓扑与权限边界
- [ ] 保留：拓扑、Boundary Note、顺序禁令
- [ ] 删除：重复角色说明句

### 2) 环境锚定与注入
- [ ] 保留 4 条核心注入项
- [ ] 压缩措辞，避免叠句

### 3) 生命周期控制
- [ ] 只保留状态推进与等待机制
- [ ] 与 Fail-Fast 重复的结果性语句可删

### 4) 模型一致性与重派
- [ ] 保留错配分流 + Retry 授权 + 上限=2
- [ ] 删除重复解释

### 5) 轨道2验收
- [ ] 保留验收矩阵、覆写模板、Delta
- [ ] 保留双轨职责注记
- [ ] 删除与 Fuse Checklist 重复提醒

### 6) Fail-Fast
- [ ] 保留触发条件清单（bullet）
- [ ] 不写重复解释段

### 7) 多模型批次
- [ ] 保留：`CHECKLIST_<Batch_ID>`、命名规范、串行推进、禁并发
- [ ] 删除延展叙述

### 8) 异常归因
- [ ] 保留三字段模板：Attribution / Evidence / Action
- [ ] 保留四类 Attribution 标签

### 9) Fuse Checklist
- [ ] 全量保留硬闸门检查项
- [ ] 仅做文案去重，不改条目语义

---

## D. 瘦身后自检（必须）

- [ ] 关键词仍存在：
  - `OPERATOR_OVERRIDE_BLOCK_START`
  - `operator_closure_gate.sh`
  - `receipts/exec_checkpoint_`
  - `manifest_<Run_ID>_round`
  - `CHALLENGE_COMPLETE`
  - `D4_FORCED_TO_ZERO`
- [ ] `diff` 结果仅体现删句/并句/编号整理，不新增新规则
- [ ] 章节可读性提升（总行数下降）

---

## E. 提交规范

- [ ] 提交信息包含 `slimdown` 关键词
- [ ] 说明“仅文案瘦身，无规则变更”
- [ ] 推送前再执行一轮自检
