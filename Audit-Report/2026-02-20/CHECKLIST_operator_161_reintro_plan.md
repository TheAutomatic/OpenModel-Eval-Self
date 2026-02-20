# CHECKLIST — 1.6.1 内容回补方案（对齐当前 1.5.2 基线）

> 目标：以当前 `WORKFLOW-ModelEval-Self-OPERATOR.md`（revert 后）为基线，回补“7点必要内容”，并避免再次删掉现有硬闸门。
> 原则：最小增量、逐段合入、每步可审计。

---

## A. 预检查（必须）
- [ ] 基线确认：当前 `OPERATOR` 版本为 `1.5.2`。
- [ ] 确认硬闸门仍在：
  - [ ] 占位符拦截检查命令仍存在（`grep -RInE "<PASS/FAIL|OPERATOR_OVERRIDE_BLOCK_START" ...`）
  - [ ] `operator_closure_gate.sh` 检查条款仍存在
  - [ ] receipt / challenge / manifest / D4 auto-check 检查条款仍存在

---

## B. 7点回补清单（分“必加/精简加/并入加”）

### 1) Operator 层定位说明（精简加）
- 目标：补 3~5 行，不展开叙事。
- 新增点：
  - [ ] “Operator 只管决策/验收，不代跑执行命令”
  - [ ] “REVIEW/EXEC 为执行细节真相源”
- 放置位置：第 1 节标题下，作为 `Boundary Note`。

### 2) 标准拓扑 + 顺序禁令（精简加）
- 目标：在现有拓扑节补“禁止项”两条。
- 新增点：
  - [ ] 禁止 Round2 先于 Round1
  - [ ] 禁止单轮替代双轮
- 放置位置：现有“架构拓扑与权限边界”末尾。

### 3) 验模与重派规则（必加）
- 目标：新增一节，短状态机风格。
- 新增点：
  - [ ] `MODEL_ECHO_MISMATCH` 异常分流（Operator 输入错 / Runtime 错）
  - [ ] `sub0` 未获 Retry 禁止自动重派
  - [ ] sub1/sub2 重派上限 = 2
- 放置位置：在 Context Injection 后，Fail-Fast 前。

### 4) 多模型批次策略（必加）
- 目标：新增“Batch Run”专节（串行为硬约束）。
- 新增点：
  - [ ] `CHECKLIST_<Batch_ID>.md` 强制
  - [ ] Batch/Run 命名规范
  - [ ] 每模型收尾后才能推进下一模型
  - [ ] 禁止并发多个 sub0
- 放置位置：Fail-Fast 后（或其前），独立章节。

### 5) 双轨评分职责（并入加，不单开大段）
- 目标：不新开大节，嵌入现有“轨道2验收”内。
- 新增点：
  - [ ] 明确“轨道1=sub0，轨道2=Operator”
  - [ ] 强调“不把轨道2失误直接扣到轨道1模型分”
- 放置位置：4.1 验收矩阵下方 2~3 条注记。

### 6) Fail-Fast 条件集（必加）
- 目标：在现有 Fail-Fast 节扩充关键触发。
- 新增点：
  - [ ] 超时无 checkpoint ACK
  - [ ] 时序倒置（R1 未闭环即进 R2）
  - [ ] 无证推进（仅文本，无工具证据）
  - [ ] 多模型并发 sub0
- 放置位置：现有 5 节下，按 bullet 增补。

### 7) 异常归因与判责记录（必加）
- 目标：新增一节 + 固定模板。
- 新增点：
  - [ ] Attribution 标签：`FAULT_OPERATOR_INPUT | FAULT_SUB0_DISPATCH | FAULT_EXEC_RUNTIME | FAULT_SPEC_AMBIGUITY`
  - [ ] 三字段：`Attribution / Evidence / Action`
  - [ ] 触发条件：错配、重派、中断、超时
- 放置位置：Fail-Fast 后、Fuse Checklist 前。

---

## C. 防回归检查（关键）
- [ ] 回补后再次确认以下条款未丢：
  - [ ] 占位符拦截 grep 条款
  - [ ] closure gate 脚本条款
  - [ ] receipt/challenge/manifest/D4 auto-check 条款
- [ ] 文档内版本号更新为：`1.6.1`
- [ ] 不改 EXEC 头部（保持“无版本号”策略）

---

## D. 提交策略（避免大坨改动）
- [ ] Commit 1：仅加“定位 + 顺序禁令 + 验模重派”
- [ ] Commit 2：仅加“多模型批次 + Fail-Fast 扩充 + 归因模板”
- [ ] Commit 3：仅做“防回归核验与措辞统一”

---

## E. 完成判定
当以下全部为真，视为 1.6.1 回补完成：
- [ ] 7点内容均已覆盖（按 B 节）
- [ ] 既有硬闸门无丢失（按 C 节）
- [ ] 文档结构未失控（新增章节 <= 3，新增内容以规则为主、少叙事）
