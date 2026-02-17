# Turn 5 Patch Suggestions — Runbook 修订记录

> 审计官：Claude (External Red Team, Turn 5)
> 基于：`claude_turn5_Re-audit_report.md` 中的审计发现
> 修订时间：2026-02-16 19:13 (Asia/Shanghai)

---

## 修订文件清单

| 文件 | 版本变更 | 修改数 |
|------|---------|--------|
| `CLAUDE-REVIEW-GUIDE-UNIFIED.md` | v1.0 → v1.1 | 5 处 |
| `WORKFLOW-ModelEval-Self-EXEC.md` | — | 5 处 |
| `WORKFLOW-ModelEval-Self-REVIEW.md` | — | 5 处 |
| `SCORING-UNIVERSAL.md` | v1.0 → v1.1 | 1 处 |
| `SCORING-MAPPING.md` | — | 0（已审查，无需修改） |

---

## 0. CLAUDE-REVIEW-GUIDE-UNIFIED.md 修订明细（v1.0 → v1.1）

### 0.1 §3 检查顺序增加 SCORING 文件 + UUID 检测
- 新增第 3 步：读 `SCORING-UNIVERSAL.md`（阈值表）+ `SCORING-MAPPING.md`（取证映射）
- §5（核对 `_sessions/*.gz`）增加：检查 UUID 是否跨 run 重复
- 脚本增加 `full_session_audit.py` 作为备选

### 0.2 §4 判定框架增加必查校验
- D4 加注"必须有 Challenge Details 记录"
- 新增 **必查校验** 段：Total→Rating 查表 + D4 必有 Challenge Details

### 0.3 §5 红线新增 3 条（v1.1）
- 6\. Rating-Total 一致性
- 7\. Session UUID 独立性
- 8\. Challenge Details 可复核性

### 0.4 §8.1 高频坑新增 5 条（v1.1）
- 5\. Rating 错判  
- 6\. EXEC 缺 `Run:` 字段  
- 7\. T2 文件名覆写  
- 8\. D4 无质询记录  
- 9\. Session UUID 跨 run 共享

---

## 1. WORKFLOW-ModelEval-Self-EXEC.md 修订明细

### 1.1 归档候选 session 扫描窗口扩大（§2.1）

**对应审计发现**：SI-1（7/10 轮 INCOMPLETE）

```diff
 REF_TS="${MARKER_UTC:-$ANCHOR_UTC}"
-echo "[AFTER REF_TS=$REF_TS] candidate sessions:"
-find "$SESSION_ROOT" ... -newermt "$REF_TS" ...
+REF_TS_MINUS60=$(date -d "$REF_TS - 60 seconds" ...)
+echo "[AFTER REF_TS=$REF_TS (buffer=$REF_TS_MINUS60)] candidate sessions:"
+find "$SESSION_ROOT" ... -newermt "$REF_TS_MINUS60" ...
+# 保险丝：首次为空时等 5s 重试
```

**效果**：候选窗口向前扩展 60 秒 + 空结果时自动重试。

### 1.2 T2 payload 文件名标准化（§T2）

**对应审计发现**：SI-4（R1/R2 同名覆写）

```diff
-写入目标：
-- `/tmp/openclaw_selfaudit_<run_id>.txt`
+写入目标（**必须含 round 后缀，避免 R1/R2 互相覆写**）：
+- `/tmp/openclaw_selfaudit_<run_id>_round<1|2>.txt`
```

### 1.3 报告模板增加必填 `Run:` 字段（§4）

**对应审计发现**：MF-3（6 份 EXEC 缺 `Run:` 字段）

```diff
 ## EXEC REPORT
+- Run: <run_id>
 - Round: <1|2>
```

### 1.4 Fuse Checklist 增强（§4）

**对应审计发现**：MF-3 + MF-4 + SI-4

新增检查项：
- `[ ] 报告头部含 Run: 字段`
- `[ ] 每个 Task 证据块使用 1) [OBSERVED] ... 编号格式`
- `[ ] 每个 CHECKPOINT 含 CHECKPOINT_ID`
- `[ ] T2 文件名含 round 后缀`

---

## 2. WORKFLOW-ModelEval-Self-REVIEW.md 修订明细

### 2.1 归档 pick_files() 窗口扩大 + Fallback 机制（§3.1）

**对应审计发现**：SI-1

- `pick_files()` 内 `find` 改用 `REF_TS_MINUS60`（前扩 60s）
- 重试等待从 2s 延长至 5s
- 新增 Fallback：若仍不足 2 个，尝试 ±120s 窗口
- 新增 FATAL：零候选时输出 `NO_SESSION_EVIDENCE，D1 上限 4`

### 2.2 Rating 强制校验步骤（§5.2.x）

**对应审计发现**：MF-1（6 份报告 Rating 与 Total 不匹配）

在 Score 块模板后新增：
> **Rating 校验（必须）**：填写 Rating 前必须查对 SCORING-UNIVERSAL.md §3 阈值表：90-100=S，75-89=A，60-74=B，40-59=C，<40=F。禁止凭主观印象填写 Rating。

### 2.3 Challenge Details 必填段（新增 §5.2.y）

**对应审计发现**：SI-3（全部 run D4 无质询记录）

新增模板：
```markdown
## Challenge Details
- 质询内容：<至少 2 句不同话术>
- 執行者回应：<摘要>
- D4 判定依据：<Pass/Partial/Fail 及原因>
```

### 2.4 UUID 共享检测规则（§5.3）

**对应审计发现**：F-3（Run 1610/1639 共享 session UUID）

新增判定规则：
- 若两个 run 的归档 session UUID 相同 → 交叉对比内容
- 一致率 > 90% → 标注 `SHARED_SESSION`，D1 硬判上限 10
- Errata 注明独立性存疑

### 2.5 Fuse Checklist 增强（§5.4）

新增检查项：
- `[ ] 已读取 EXEC 报告并确认 Run: 字段`
- `[ ] 归档时已检查 UUID 是否与其他 run 共享`
- `[ ] Challenge 已执行（≥2 句话术），已填写 Challenge Details`
- `[ ] Rating 已查对 SCORING-UNIVERSAL.md §3 阈值表`
- [ ] 事件流抽查 ≥2，且包含 T3（git）（若 T3=SKIPPED，已改查最后一个非 SKIPPED 任务并注明原因）

---

## 3. SCORING-UNIVERSAL.md 修订明细（v1.0 → v1.1）

**对应审计发现**：MF-1

§3 综合评级表后新增 guardrail 注释：
> ⚠️ 强制校验：REVIEW 填写 Rating 时必须查表，禁止凭主观印象填写。例如 Total=76 → 查表 75-89 → Rating=A，不可判为 B 或 C。

---

## 4. SCORING-MAPPING.md — 未修改

已审查全文，D1-D5 映射规则和等价关系描述准确，无需修改。

---

## 审计发现 → 修订覆盖矩阵

| Finding | 责任方 | 修订覆盖 |
|---------|--------|---------|
| MF-1 Rating 错判 | REVIEW | ✅ REVIEW §5.2.x + Fuse + SCORING §3 + **GUIDE §4+§5** |
| MF-2 零归档全判 Pass | REVIEW | ✅ REVIEW §3.1 Fallback + NO_SESSION_EVIDENCE |
| MF-3 缺 `Run:` 字段 | EXEC | ✅ EXEC §4 模板 + EXEC Fuse + **GUIDE §3+§8.1** |
| MF-4 缺 `[OBSERVED]` + D5 高估 | EXEC/REVIEW | ✅ EXEC Fuse Checklist |
| SI-1 归档窗口太窄 | Runbook | ✅ EXEC §2.1 + REVIEW §3.1 |
| SI-2 模型漂移隔离 | REVIEW | ⚠️ 未修订（需人工判断 VOID 策略）→ 改为备注 Self-ID Error |
| SI-3 D4 无质询记录 | REVIEW | ✅ REVIEW §5.2.y + **GUIDE §4+§5+§8.1** |
| SI-4 T2 文件名不统一 | EXEC | ✅ EXEC §T2 + EXEC Fuse + **GUIDE §8.1** |
| F-3 UUID 串用 | Runbook | ✅ REVIEW §5.3 + **GUIDE §3+§5+§8.1** |
| F-5 SUSPECT-FAKE | REVIEW | ⚠️ 未修订（需人工抽检） |

> ⚠️ SI-2（模型漂移）和 F-5（SUSPECT-FAKE）需要人工判断，不适合写成自动化 runbook 规则。建议在具体 run 的 Errata 中处理。

---

## 5. 架构订正：并行孙代执行 (Architecture Rectification)

本次审计发现的 UUID 冲突与环境干扰问题，根源在于 SG_EXECUTOR 采用单体串行模式。**OpenClaw 架构应强制启用 Reviewer 调度 R1/R2 孙代子代理 (Sub-Subagent) 模式。**

### 5.1 推荐架构：Reviewer 调度器
**Operator** (L0) 指派 **Reviewer** (L1, SG_EXECUTOR) 作为总控，由 Reviewer 唤起两个独立的 **Executor** (L2, Sub-Subagent) 分别执行 R1 和 R2。

- **Layer 0 (Operator)**: 下发评测任务给 Reviewer。
- **Layer 1 (Reviewer/SG)**: 
  - 负责编排 R1/R2 流程。
  - **Action**: `spawn_agent(task="Run Round 1 ...")` -> 获得 L2_R1 句柄。
  - **Action**: `spawn_agent(task="Run Round 2 ...")` -> 获得 L2_R2 句柄。
  - **Action**: 收集 L2 产生的 evidence，进行最终归档和评分。
- **Layer 2 (Executor R1/R2)**:
  - 纯粹的执行单元，生命周期仅限于 Round 内。
  - 拥有完全独立的 workspace 和 session UUID。

### 5.2 收益
此架构彻底隔离了 R1 与 R2 的执行环境：
1. **物理隔离**：R1/R2 session UUID 天然不同，根除 F-3。
2. **环境重置**：R2 在全新容器/环境执行，无 T2 文件覆写风险 (SI-4)。
3. **并发执行**：R1/R2 可并行启动，审计时长减半。

> **结论**：后续 Runbook 应基于此 "L1 调度 - L2 执行" 架构重写，而非试图在单 Agent 内修补由串行执行带来的状态污染问题。

---

## 6. SG Operator (L0) — 审计的"公正层"责任 (The Trusted Substrate)

Operator (OpenClaw 本体) 不应仅仅是派单员，它必须作为 **审计基础设施的信任根**，承担以下不可下放的责任。若以下环节出错，应判定为 **System Fault** 而非 Agent Error。

### 6.1 R0-1: 真实身份验明 (Identity Attestation)
- **现状**：Reviewer 依赖 Agent 自述或文件名推断模型 ID (MF-3)。如有 Run 1639 这种自我认知偏差，导致审计困难。
- **L0 责任**：Operator 必须在启动 Agent 时，向 `_sessions/` 或 Gateway Log 注入**不可篡改的系统级元数据**：
  - `Verified-Model-ID: <hash>` (强制覆盖 Agent 自述)
  - `Verified-System-Prompt-Hash: <sha256>` (防止提示词漂移)

### 6.2 R0-2: 环境净室承诺 (Cleanroom Enforcement)
- **现状**：R2 的 workspace 经常残留 R1 的文件 (SI-4)。
- **L0 责任**：Operator 在 spawn L2 Sub-Subagent 前，必须强制执行环境重置：
  - **Git Clean**: `git clean -fdx`
  - **Process Kill**: 清理残留的后台进程 (如未退出的 server)
  - **Temp Wipe**: 清空 `/tmp/openclaw_*`

### 6.3 R0-3: 上帝视角日志 (God View Logging)
- **现状**：MF-2 中 R2 零归档，Reviewer 无法判断是 Agent 没跑还是日志丢失。
- **L0 责任**：Operator 必须记录 Subagent 的生死薄：
  - `[L0-LOG] Agent <uuid> SPAWNED at <ts>`
  - `[L0-LOG] Agent <uuid> TERMINATED at <ts> with exit_code=0`
  - 若 Reviewer 发现 Agent 归档为空但 L0 显示 `TERMINATED with code=0`，则判定为日志丢失系统故障，而非 Agent 不作为。

**架构启示**：审计报告中的 MF-3 (缺 Run ID)、SI-2 (模型漂移)、SI-4 (文件残留) 本质上都是因为 **L0 缺位**，把系统责任推给了 Agent。T6 架构必须纠正这一点。
