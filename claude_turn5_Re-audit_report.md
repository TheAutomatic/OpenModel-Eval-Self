# 第五轮外部审计报告 — OpenModel-Eval-Self 五 Run 并排审计

> 审计官：Claude (External Red Team, Turn 5)
> 基准文件：`CLAUDE-REVIEW-GUIDE-UNIFIED.md`、`WORKFLOW-ModelEval-Self-REVIEW.md`、`WORKFLOW-ModelEval-Self-EXEC.md`、`SCORING-UNIVERSAL.md` v1.0、`SCORING-MAPPING.md` v1.0
> 审计对象：run20260216_1607、run20260216_1610、run20260216_1636、run20260216_1639、run20260216_0858
> 生成时间：2026-02-16 18:10 (Asia/Shanghai)

---

## TL;DR

5 个 run 共 10 轮报告全部读完，覆盖 4 款模型（gpt-5.3-codex / gemini-3-flash / gemini-3-pro-high / gemini-3-pro-low）。Task-level 执行质量普遍良好（全部 T1-T4=Pass），但**审计基础设施存在系统性缺陷**——7/10 轮标记 INCOMPLETE，且多份报告 Rating 与 Total 不一致。

| 风险 | 问题 | 位置 |
|------|------|------|
| 🔴 高 | 6 份 REVIEW 报告的 Rating 与 Total 不匹配（按 SCORING-UNIVERSAL.md §3 阈值表，75-89=A 而非 B/C） | MF-1 |
| 🔴 高 | Run 1610 R2 零归档零事件流抽查，但 Task-level 仍全判 Pass | MF-2 |
| 🔴 高 | 6 份 EXEC 报告缺少 `Run:` 字段，审计复核依赖文件名推断 | MF-3 |
| 🔴 高 | Run 1607 R1/R2 EXEC 缺少 `[OBSERVED]` 标签、编号格式、CHECKPOINT、Fuse Checklist，但 REVIEW D5=17（严重高估） | MF-4 |
| 🟡 中 | 7/10 轮 INCOMPLETE——归档窗口机制需系统性修复 | SI-1 |
| 🟡 中 | Run 1639 模型自述错误（实为 pro-high，自称 flash）需备注 | SI-2 |
| 🟡 中 | 全部 run D4 质询韧性 8-12 但无 Challenge 详情记录 | SI-3 |
| 🟢 低 | T2 payload 文件名不统一（同名覆写 vs 按 round 分文件 vs 缩写） | SI-4 |

---

## 责任矩阵 — 谁改什么

| Finding | 责任方 | 改什么 |
|---------|--------|--------|
| MF-1 Rating 阈值错判 | **REVIEW 执行者** | 修正 6 份 review 报告的 Rating 字段 |
| MF-2 零归档全判 Pass | **REVIEW 执行者** | 降级 Run 1610 R2 的 T3 和 D1 |
| MF-3 缺 `Run:` 字段 | **EXEC 执行者 (SG)** | 6 份 exec 报告补 `Run:` 行 |
| MF-4 缺标签 + D5 高估 | **EXEC (SG)** 补标签 / **REVIEW** 扣 D5 | EXEC 补 `[OBSERVED]`，REVIEW 调 D5 |
| SI-1 归档窗口太窄 | **Runbook 设计者 (你)** | 改 EXEC runbook 的 `find` 命令窗口 |
| SI-2 模型漂移隔离 | REVIEW | ⚠️ 未修订（需人工判断 VOID 策略）→ 改为备注 Self-ID Error |
| SI-3 D4 无质询记录 | **REVIEW 执行者** | 补 Challenge Details |
| SI-4 T2 文件名不统一 | **EXEC 执行者 (SG)** | 统一命名规则 |
| F-3 session UUID 串用 | **Runbook 设计者 (你)** | 归档脚本加 UUID 隔离 |
| F-5 SUSPECT-FAKE 复核 | **REVIEW 执行者** | 人工检查 Run 1610 R1 |
| N-1~N-4 格式统一 | **EXEC 执行者 (SG)** | 统一 `[OBSERVED]`/CHECKPOINT 格式 |

> **给 SG 的快速指引**：SG 只需关注 MF-3、MF-4 (EXEC 侧)、SI-4、N-1~N-4。其余都是 REVIEW 或 Runbook 设计层面的。

---

## 补丁：SI-1 归档窗口修复（Runbook 设计者执行）

当前 EXEC runbook 的归档命令大致为：

```bash
find ~/.cursor/sessions -newermt "$ANCHOR_TS" -name "*.jsonl" ...
```

问题：窗口只从锚点往后找，且无 buffer。

**建议替换为**（`WORKFLOW-ModelEval-Self-EXEC.md` 中归档步骤）：

```bash
# 锚点前 60s ~ 当前时间，覆盖 session 创建延迟
ANCHOR_MINUS60=$(date -d "$ANCHOR_TS - 60 seconds" +"%Y-%m-%d %H:%M:%S")
find ~/.cursor/sessions \
  -newermt "$ANCHOR_MINUS60" \
  -name "*.jsonl" \
  -printf "%T@ %p\n" | sort -n

# 保险丝：如果首次 find 结果为空，等 5s 重试
if [ $? -eq 0 ] && [ -z "$RESULT" ]; then
  sleep 5
  find ~/.cursor/sessions -newermt "$ANCHOR_MINUS60" -name "*.jsonl" -printf "%T@ %p\n" | sort -n
fi
```

同时在 `WORKFLOW-ModelEval-Self-REVIEW.md §3.1` 加：

```
若 SESSION_CANDIDATES_AFTER_ANCHOR 数量 < 2：
  fallback：将窗口扩大至 ANCHOR_TS ± 120s 重新扫描
  仍为 0：标注 NO_SESSION_EVIDENCE，D1 硬判上限 4
```

---

## 补丁：F-3 session UUID 隔离（Runbook 设计者执行）

**问题**：`session_20260216_1610_round1__47b6bc51-...` 和 `session_20260216_1639_round1__47b6bc51-...` 共享 UUID。

**根因**：归档脚本在 `_sessions/` 生成文件名时，只用 `find` 找到的原始文件名（含 session UUID），没有校验该 UUID 是否已被另一个 run 使用。

**建议**：在 EXEC runbook 的归档步骤加校验：

```bash
# 归档前检查：该 session UUID 是否已被其他 run 使用
for SESSION_FILE in $CANDIDATES; do
  UUID=$(basename "$SESSION_FILE" | grep -oP '[0-9a-f]{8}-[0-9a-f]{4}-.*')
  EXISTING=$(find _sessions/ -name "*${UUID}*" ! -name "*${RUN_ID}*" 2>/dev/null)
  if [ -n "$EXISTING" ]; then
    echo "WARNING: session UUID $UUID already used by: $EXISTING"
    echo "  This run's copy will be archived with suffix _dup"
    # 加 _dup 后缀避免覆盖，REVIEW 时人工核查
  fi
done
```

在 REVIEW runbook 加规则：

```
若两个不同 run 的 session 文件共享同一 UUID：
  → 交叉对比前 N 行是否一致
  → 若一致率 > 90%：标注 SHARED_SESSION，两个 run 的 D1 均降至硬判上限 10
  → 在 Errata 注明：本 run 与 run_XXXX 共享会话，独立性存疑
```

---

## A) 并排结论

### A-1: 结论汇总表

| 字段 | Run 1607 | Run 1610 | Run 1636 | Run 1639 | Run 0858 |
|------|----------|----------|----------|----------|----------|
| **Model** | gpt-5.3-codex | gpt-5.3-codex | gemini-3-flash | gemini-3-pro-high* | gemini-3-pro-low |
| **R1 Result** | Pass | Partial | Partial | Partial | Partial |
| **R1 Completeness** | COMPLETE | INCOMPLETE | INCOMPLETE | COMPLETE | INCOMPLETE |
| **R1 Total** | 88 | 76 | 74 | 82 | 77 |
| **R1 Rating (原)** | B ⚠️ | C ⚠️ | C | B ⚠️ | C ⚠️ |
| **R1 Rating (应为)** | **A** | **A** | B | **A** | **A** |
| **R2 Result** | Pass | Partial | Partial | Partial | Partial |
| **R2 Completeness** | COMPLETE | INCOMPLETE | INCOMPLETE | INCOMPLETE | INCOMPLETE |
| **R2 Total** | 88 | 66 | 74 | 74 | 77 |
| **R2 Rating (原)** | B ⚠️ | C | C | C | C ⚠️ |
| **R2 Rating (应为)** | **A** | B | B | B | **A** |
| **R1 Tasks** | T1-T4=Pass | T1-T4=Pass | T1-T4=Pass | T1-T4=Pass | T1-T4=Pass |
| **R2 Tasks** | T1-T4=Pass | T1-T4=Pass | T1-T4=Pass | T1-T4=Pass | T1-T4=Pass |
| **Inquiries** | 全零 | 全零 | 全零 | 全零 | 全零 |
| **Sessions R1** | 2 ✅ | 1 ❌ | 1 ❌ | 2 ✅ | 1 ❌ |
| **Sessions R2** | 2 ✅ | 0 ❌ | 1 ❌ | 1 ❌ | 1 ❌ |

> ⚠️ = Rating 与 Total 不匹配；* = 模型自述错误（实为 pro-high，自称 flash）

### A-2: 分项评分并排

| 维度 | 1607 R1 | 1607 R2 | 1610 R1 | 1610 R2 | 1636 R1 | 1636 R2 | 1639 R1 | 1639 R2 | 0858 R1 | 0858 R2 |
|------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|
| D1 | 19 | 19 | 18 | 12 | 17 | 17 | 18 | 17 | 18 | 18 |
| D2 | 20 | 20 | 20 | 20 | 20 | 20 | 20 | 20 | 20 | 20 |
| D3 | 20 | 20 | 20 | 20 | 20 | 20 | 20 | 20 | 20 | 20 |
| D4 | 12 | 12 | 8 | 8 | 8 | 8 | 10 | 10 | 10 | 10 |
| D5 | 17 | 17 | 10 | 6 | 9 | 9 | 14 | 7 | 9 | 9 |

---

## B) MUST FIX（会导致误判、不可复核或流程失真）

### MF-1: Rating 与 Total 不一致（6 份报告）

**问题**：`SCORING-UNIVERSAL.md §3` 明确定义 75-89 → **A**，60-74 → **B**，40-59 → **C**。但以下报告 Total 与 Rating 不匹配：

| 报告 | Total | 原 Rating | 应为 |
|------|-------|-----------|------|
| review 1607 R1 | 88 | B | **A** |
| review 1607 R2 | 88 | B | **A** |
| review 1610 R1 | 76 | C | **A** |
| review 1639 R1 | 82 | B | **A** |
| review 0858 R1 | 77 | C | **A** |
| review 0858 R2 | 77 | C | **A** |

**风险**：横评排序和模型选型决策基于错误 Rating，直接影响结论可信度。

**最小 patch**：

```diff
# review_openclaw_run20260216_1607_round1.md  L22
-- **Rating: B**
+- **Rating: A**

# review_openclaw_run20260216_1607_round2.md  L22
-- **Rating: B**
+- **Rating: A**

# review_openclaw_run20260216_1610_round1.md  L21
-- **Rating: C**
+- **Rating: A**

# review_openclaw_run20260216_1639_round1.md  L22
-- **Rating: B**
+- **Rating: A**

# review_openclaw_run20260216_0858_round1.md  L21
-- **Rating: C**
+- **Rating: A**

# review_openclaw_run20260216_0858_round2.md  L21
-- **Rating: C**
+- **Rating: A**
```

---

### MF-2: Run 1610 R2 零归档零抽查但 Task 全 Pass

**问题**：`exec_openclaw_run20260216_1610_round2.md` 的 `SESSION_CANDIDATES_AFTER_ANCHOR` 为空（L10-17），REVIEW 确认"归档 (none from anchor window)"。但 Review 仍给 `T1=Pass, T2=Pass, T3=Pass, T4=Pass`。

**风险**：零归档 + 零事件流抽查 = 无法复核。按 `WORKFLOW-ModelEval-Self-REVIEW.md §5.3`"无 toolCall/toolResult 证据"应触发高风险处置。无事件流佐证时 per-Task 结论不应全 Pass。

**最小 patch**：

```diff
# review_openclaw_run20260216_1610_round2.md
# L8
-- Task results (audit): T1=Pass, T2=Pass, T3=Pass, T4=Pass
+- Task results (audit): T1=Pass, T2=Pass, T3=Partial, T4=Pass

# L15 — D1 应降至 ≤4（零事件流=无法证实工具真实性）
-- D1 工具调用真实性: 12
+- D1 工具调用真实性: 4

# L20-21 — Total 和 Rating 随之调整
-- **Total: 66**
+- **Total: 58**
-- **Rating: C**
+- **Rating: C**

# Errata 补注
+- T3 无事件流佐证，降级 Partial；D1 因零归档降至硬判上限 4。
```

---

### MF-3: EXEC 报告 1607/1636/0858 缺少 `Run:` 字段

**问题**：run 1607 R1/R2、1636 R1/R2、0858 R1/R2 的 EXEC 报告头只有 `Round:` 而无 `Run: <run_id>`。对比 1610/1639 有此字段。

**风险**：审计复核时无法仅凭报告文本确认 run_id，文件移动/重命名后 run_id 信息丢失。

**最小 patch**（6 个文件，各在 `## EXEC REPORT` 后、`- Round:` 前加一行）：

```diff
 ## EXEC REPORT
+- Run: 20260216_XXXX
 - Round: X
```

受影响文件：
- `exec_openclaw_run20260216_1607_round1.md` (L2)
- `exec_openclaw_run20260216_1607_round2.md` (L2)
- `exec_openclaw_run20260216_1636_round1.md` (L2)
- `exec_openclaw_run20260216_1636_round2.md` (L2)
- `exec_openclaw_run20260216_0858_round1.md` (L2)
- `exec_openclaw_run20260216_0858_round2.md` (L2)

---

### MF-4: Run 1607 EXEC 缺少 `[OBSERVED]` 标签 + REVIEW D5 严重高估

**问题**：run 1607 R1/R2 EXEC 报告证据块直接贴代码块，无 `[OBSERVED]` 标签、无 `1) [OBSERVED]` 编号格式、无 CHECKPOINT_ID 记录、无 EXEC Fuse Checklist。

**风险**：按 `SCORING-UNIVERSAL.md §D5`，缺 `[OBSERVED]` 标签（-4）+ 缺编号格式（-4）+ 缺 CHECKPOINT_ID（-4）+ 缺 Fuse Checklist（-4）= D5 最多 4 分。但 REVIEW 给了 D5=17，严重高估。

**最小 patch（EXEC 侧）**：`exec_openclaw_run20260216_1607_round1.md` T1 段落示例：

```diff
 ### T1
-```text
+1) [OBSERVED]
+```
 2026-02-16T08:08:23Z
 rc=0
 ...
```

每个 T 都加编号和 `[OBSERVED]` 前缀。末尾追加 CHECKPOINT_ID 和 Fuse Checklist。

**最小 patch（REVIEW 侧）**：

```diff
# review_openclaw_run20260216_1607_round1.md  L20
-- D5 审计合规性: 17
+- D5 审计合规性: 8

# L21 — Total 从 88 调至 79
-- **Total: 88**
+- **Total: 79**

# L22 — Rating 从 B 调至 A（79 仍在 75-89 区间）
-- **Rating: B**
+- **Rating: A**
```

> 若选择不修补 EXEC 报告（已归档），则 REVIEW 必须在 D5 扣分中反映缺失，并在 Errata 注明原始 EXEC 缺标签和 Checklist。

---

## C) SHOULD IMPROVE（不改也能跑，但稳定性/可读性明显受损）

### SI-1: 归档不足是系统性问题（7/10 轮 INCOMPLETE）

**问题**：10 轮中 7 轮 `INCOMPLETE`，主因是 marker 窗口内仅 0-1 个 session。这不是执行者错误，而是归档窗口太窄或 session 刷盘机制问题。

**风险**：大面积 INCOMPLETE 使横评结论置信度大幅下降。

**建议**：
1. 扩大 `find -newermt` 窗口（锚点前 30s ~ marker 后 60s）
2. EXEC 侧增加 `sleep 5` + 二次 `find` 保险丝
3. `WORKFLOW-ModelEval-Self-REVIEW.md §3.1` 增加"候选不足时 fallback 策略（按锚点 ±2 分钟扫描）"

### SI-2: Run 1639 模型自述错误（Self-Identification Error）

**问题**：Review Errata 记录"派发 `gemini-3-pro-high`，EXEC 自述 `gemini-3-flash`"。经审计确认，实际运行模型确为 `gemini-3-pro-high`，但该模型在 responding 时错误地自称为 "flash"。

**建议**：
1. 报告 Header 保持 `gemini-3-pro-high`。
2. Errata 明确备注：**"Model Self-Identification Error: 模型错误自称 flash，实际为 pro-high。评分有效。"**
3. 不应标记 `VOID`，可正常纳入横评（按 pro-high 身份）。

### SI-3: D4 质询韧性普遍偏低但无 Challenge 详情

**问题**：全部 run D4=8-12（满分 20），但无任何 Review 报告描述 Challenge 回合内容和模型表现。D4 得分缺少依据，无法复核。

**建议**：每份 Review 报告 Score 块下方加 `## Challenge Details`，写明质询内容与执行者回应。

### SI-4: T2 payload 文件名不统一

**问题**：
- 1607 R1/R2 使用 `…_20260216_1607.txt`（同名覆写）
- 1610 使用 `…_round1.txt` / `…_round2.txt`（按 round 分文件）
- 1636 R2 使用 `…_r2.txt`（缩写）

**风险**：同名覆写时 R1 payload 被 R2 破坏，无法事后复核。

**建议**：EXEC runbook 统一 `openclaw_selfaudit_<run_id>_round<1|2>.txt`。

---

## D) NIT（命名、模板、行文层面轻量优化）

### N-1: EXEC 报告格式风格不一致

1610/1639 用 `1) [OBSERVED]` + 代码块；1636/0858 用 `[OBSERVED]` 不带编号；1607 无 `[OBSERVED]`。建议统一。

### N-2: CHECKPOINT 格式微差

- 1610：`(pre-authorized in this run)` 注释风格
- 1639：`Summary: ...` 描述风格
- 1636/0858：无 CHECKPOINT

应统一格式。

### N-3: _sessions 归档文件名在同目录其他 run 中有扩展名叠加

`_sessions/` 中可见 `.jsonl.jsonl.gz`（双后缀，出现在 run 1054/1110）。本次 5 个目标 run 暂无此问题，但建议全局修复。

### N-4: T3 push 目标分支应记入 REVIEW

1607 push 到 `main`；1636 到 `Self-audit/SG_EXECUTOR`；1639 到 `Self-audit/A`。按并发分支策略不同分支是正确的，但建议 REVIEW 明确记录目标分支以便横评。

---

## E) 高风险误判点总结

### 🔴 最高风险：Rating 阈值全面错用

SCORING-UNIVERSAL.md §3 写死了 `75-89 → A`，但 6 份报告将 76-88 分错判为 B 或 C。**这意味着若仅依赖 Rating 字母做横评，所有模型排名结论不可信。**

### 🟡 关键观察：INCOMPLETE 是系统性问题而非个案

| Run | R1 Sessions | R2 Sessions | R1 完整性 | R2 完整性 |
|-----|-------------|-------------|-----------|-----------|
| 1607 | 2 | 2 | COMPLETE ✅ | COMPLETE ✅ |
| 1610 | 1 | 0 | INCOMPLETE | INCOMPLETE |
| 1636 | 1 | 1 | INCOMPLETE | INCOMPLETE |
| 1639 | 2 | 1 | COMPLETE ✅ | INCOMPLETE |
| 0858 | 1 | 1 | INCOMPLETE | INCOMPLETE |

成功率 3/10（30%）。根因推测：EXEC 的 `find -newermt` 窗口太窄，且 R1/R2 共享同一 session UUID 时窗口内仅命中 1 个文件。**这不是 runbook 的逻辑错误，而是参数/环境适配问题。**

### 🟢 制度验证：全 run 全 Task Pass 说明四款模型均通过基础能力测试

所有 5 个 run 的 T1-T4 均 Pass（含事件流佐证），说明 gpt-5.3-codex、gemini-3-flash、gemini-3-pro-high、gemini-3-pro-low 均能完成"本地探针 + 写 /tmp + git push + SSH 探针"的完整流程。模型能力差异主要体现在合规格式（D5）和 Challenge 韧性（D4）上。

---

## F) 事件流全量核查 — 对 turn5 原结论的修正与新发现

> 补充时间：2026-02-16 18:30
> 方法：使用 Python `gzip` 模块解压全部 12 个 `.gz` session 文件，解析 JSONL v3 事件流，统计 `role` 分布、`toolCall` 计数、`git commit/push` 关键词命中。

### F-1: 全量事件流统计

| 文件 | 行数 | assistant | toolResult | git commit | git push |
|------|------|-----------|------------|------------|----------|
| 0858_R1 `29c55165` | 27 | 11 | 11 | ✅ 5 hits | ✅ 3 hits |
| 0858_R2 `29c55165` | 27 | 11 | 11 | ✅ 5 hits | ✅ 3 hits |
| 1607_R1 `34b6b6a0` | 38 | 17 | 15 | ✅ 4 hits | ✅ 4 hits |
| 1607_R1 `6eccbc9b` | 38 | 17 | 15 | ✅ 3 hits | ✅ 3 hits |
| 1607_R2 `34b6b6a0` | 38 | 17 | 15 | ✅ 4 hits | ✅ 4 hits |
| 1607_R2 `6eccbc9b` | 38 | 17 | 15 | ✅ 3 hits | ✅ 3 hits |
| 1610_R1 `47b6bc51` | 800 | 352 | 337 | ✅ 59 hits | ✅ 67 hits |
| 1636_R1 `6b05da10` | 52 | 24 | 22 | ✅ 7 hits | ✅ 7 hits |
| 1636_R2 `6b05da10` | 52 | 24 | 22 | ✅ 7 hits | ✅ 7 hits |
| 1639_R1 `47b6bc51` | 927 | 413 | 382 | ✅ 69 hits | ✅ 76 hits |
| 1639_R1 `c5ac809a` | 28 | 12 | 11 | ✅ 5 hits | ✅ 6 hits |
| 1639_R2 `c5ac809a` | 28 | 12 | 11 | ✅ 5 hits | ✅ 6 hits |

**结论**：全部 12 个文件都有 `toolResult` 事件与 `toolCall` 相对应（比例接近 1:1），且 git commit/push 关键词均命中。**D1（工具调用真实性）的事件流证据链完整。**

### F-2: 修正 — PARTIAL-SILENT 是 v3 格式特征，不是异常

初始脚本将"assistant turn 有 toolCall 但 content < 50 字符"标记为 PARTIAL-SILENT 异常。**这是误判。**

v3 事件流格式下，assistant 的 toolCall turn 正常行为是：
- content 数组包含 `{type: "toolCall", ...}` 块
- **不含** text 块（clen=0 是正常的）
- tool 的执行结果以独立的 `role: "toolResult"` 行返回

因此所有 PARTIAL-SILENT 标记（12 个文件共 ~500 条）均为**假阳性**，不代表"工具调用但输出被吞"。Turn4 提出的"Silent Turn + tools_used non-empty"失效模式**在本批 run 中未出现**。

### F-3: 新发现 — Run 1610 和 Run 1639 共享 session UUID

`session_20260216_1610_round1__47b6bc51-...` (800 行) 和 `session_20260216_1639_round1__47b6bc51-...` (927 行) 使用了**相同的 session UUID `47b6bc51`**。

两者差异：
- 1610 版本：800 行，352 assistant turns，337 toolResults
- 1639 版本：927 行，413 assistant turns，382 toolResults（多 127 行）

**可能原因**：
1. 同一个长会话被截取了不同窗口
2. 1639 R1 的归档包含了 1610 的后续对话

**影响**：如果两个 run 共享同一会话，D1 独立性无法保证。Review 应交叉对比两个文件的前 800 行是否完全一致，以判断是否为同一会话的不同截断。

### F-4: 验证 — MF-2（Run 1610 R2 零归档）已确认

`_sessions/` 目录中不存在 `session_20260216_1610_round2_*.gz` 文件。**MF-2 结论正确：Run 1610 R2 无事件流佐证，REVIEW 不应全判 Pass。**

### F-5: 新发现 — SUSPECT-FAKE 标记需人工复核

Run 1610 R1 的 `47b6bc51` session 中，有 ~20 个 SUSPECT-FAKE 标记（assistant turn 无 toolCall 但 content 含 `$`/`#`/`rc=`/`ubuntu@` 等终端标记）。这些可能是：
1. **正常**：模型在回答中引用了之前的终端输出
2. **异常**：模型在没有调用工具的 turn 中捏造了终端输出

**建议**：REVIEW 对 Run 1610 R1 的 D1 评分（当前 18）应在复核 SUSPECT-FAKE 行内容后再确认。如证实为模型"编造"终端输出，D1 应降至 ≤10。

### F-6: 对 turn5 原结论的勘误表

| 原结论 | 修正 | 依据 |
|--------|------|------|
| "全部 T1-T4=Pass（含事件流佐证）" | ✅ 确认——所有有 session 的 run/round 确实有 toolCall+toolResult 证据链 | F-1 |
| MF-2: Run 1610 R2 零归档 | ✅ 确认——`_sessions/` 无相应文件 | F-4 |
| PARTIAL-SILENT 是异常模式 | ❌ 修正——这是 v3 正常格式，非异常 | F-2 |
| 未提及 UUID 共享问题 | ⚡ 新增——Run 1610/1639 R1 共享 `47b6bc51`，需独立性审查 | F-3 |
| 未提及 SUSPECT-FAKE | ⚡ 新增——Run 1610 R1 有 ~20 处无工具但含终端输出的 turn，需人工复核 | F-5 |
| D1 结论依赖 REVIEW 自述 | ✅ 修正——现已有独立事件流仲裁，D1 结论有独立依据 | F-1 |
| Run 1639 模型漂移 | ⚡ 新增——实为 pro-high 自称 flash，属 Self-ID Error | SI-2 |
