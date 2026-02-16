# OpenModel-Eval-Self

Runbooks and artifacts for evaluating OpenClaw integrated model reliability.

## Folders

### `Audit-Report/`
All self-audit outputs live here, organized by date:

- `Audit-Report/YYYY-MM-DD/exec_openclaw_run<run_id>_round<round>.md` — executor (subagent) evidence report
- `Audit-Report/YYYY-MM-DD/review_openclaw_run<run_id>_round<round>.md` — reviewer (main session) audit verdict
- `Audit-Report/YYYY-MM-DD/_sessions/` — `.gz` archives of OpenClaw session JSONL files used as arbitration evidence

This repo is the **single source of truth** for audit artifacts; do not write new audit outputs into the global workspace `memory/`.

## Runbooks
- `WORKFLOW-ModelEval-Self-REVIEW.md` — reviewer workflow (DIRECT_EXEC local sub-subagent mode)
- `WORKFLOW-ModelEval-Self-EXEC.md` — executor workflow (single-round, DIRECT_EXEC)

## External Reviewer Guide
- `CLAUDE-REVIEW-GUIDE-UNIFIED.md` — unified external review guide

---

## 2026-02-16 Legacy vs Recalibrated 评分对比（v1.1）

> 口径：`SCORING-UNIVERSAL.md v1.1`
> 详细对比文件：`Audit-Report/2026-02-16/scoring_comparison_legacy_vs_recalibrated.md`
> 说明：本次为**评分口径修正**，未重跑执行任务。

### 模型总览

| 模型 | 有效样本 | Legacy Rating | Recalibrated Rating |
|---|---:|---|---|
| `openai-codex/gpt-5.3-codex` | 4 轮 | B, B, C, C | **A, A, A, B** |
| `google-antigravity/gemini-3-flash` | 2 轮 | C, C | **B, B** |
| `google-antigravity/gemini-3-pro-high` | 2 轮 | B, C | **A, B** |
| `google-antigravity/gemini-3-pro-low` | 2 轮 | C, C | **A, A** |

### Run 明细

| Run | 模型 | R1 Total | R1 Legacy→New | R2 Total | R2 Legacy→New |
|---|---|---:|---|---:|---|
| `20260216_1607` | gpt-5.3-codex | 88 | B → **A** | 88 | B → **A** |
| `20260216_1610` | gpt-5.3-codex | 76 | C → **A** | 66 | C → **B** |
| `20260216_1636` | gemini-3-flash | 74 | C → **B** | 74 | C → **B** |
| `20260216_1639` | gemini-3-pro-high | 82 | B → **A** | 74 | C → **B** |
| `20260216_0858` | gemini-3-pro-low | 77 | C → **A** | 77 | C → **A** |

### 排除样本（不纳入统计）

| Run | 原因 |
|---|---|
| `20260216_1647` | 仓库/推送路径跑偏（无效样本） |
| `20260216_0854` | 仓库/推送路径跑偏（无效样本） |

---

## 最终选型建议（当前批次）

> 结论基于“有效样本 + 评分口径修正后结果”，并结合审计完整性稳定性。

### 推荐分层

| 分层 | 模型 | 建议 |
|---|---|---|
| **主力（默认）** | `openai-codex/gpt-5.3-codex` | 综合稳定性最好（含 `1607` 双轮 A/A），优先作为主评测执行模型 |
| **强备选** | `google-antigravity/gemini-3-pro-low` | 当前样本 A/A，执行稳定，可作为主力备份或并行复核模型 |
| **可用备选** | `google-antigravity/gemini-3-pro-high` | A/B，可用；存在一次 self-ID 漂移（报告层需持续做模型一致性核验） |
| **谨慎使用** | `google-antigravity/gemini-3-flash` | 当前仅 B/B，适合轻量任务或成本优先场景，不建议做主审计基模 |

### 执行策略建议

1. 默认主链路：`gpt-5.3-codex`
2. 关键 run 双轨复核：`gpt-5.3-codex` + `gemini-3-pro-low`
3. 当出现模型自述漂移时：以系统元数据为真相源，报告侧记录 `Model consistency`
4. 无效样本（路径/仓库跑偏）继续执行“直接剔除，不入横评”规则

---

## 子孙代理异构模型能力探针（2026-02-17）

> 目标：验证主会话 / 子代理 / 孙代理可使用不同模型（异构链路）

### 探针结果表

| 层级 | 目标模型 | 最终模型 | 状态 | 备注 |
|---|---|---|---|---|
| 主会话 | `openai-codex/gpt-5.3-codex` | `openai-codex/gpt-5.3-codex` | 基线 | 作为主控模型 |
| 子代理 (L1) | （默认派生） | `nvidia-nim/z-ai/glm4.7` | ✅ SUCCESS | 子层已与主层异构 |
| 孙代理 (L2) | `qwen-portal/coder-model` | `qwen-portal/coder-model` | ✅ SUCCESS | 工具探针 OK |
| 孙代理 (L2) | `nvidia-nim/z-ai/glm4.7` | `nvidia-nim/z-ai/glm4.7` | ✅ SUCCESS | 工具探针 OK |
| 孙代理 (L2) | `google-antigravity/gemini-3-flash` | `google-antigravity/gemini-3-flash` | ✅ SUCCESS | 工具探针 OK |
| 孙代理 (L2) | `openai-codex/gpt-5.3-codex-spark4` | fallback to default | ❌ FAILED | `model not allowed` |
| 孙代理 (L2) | `openai-codex/gpt-5.3-codex-spark` | N/A | ❌ FAILED | ChatGPT account 模式不支持该模型 |

### 结论

- 已证明 OpenClaw 支持 **主/子/孙异构模型** 执行。
- 成功样本覆盖 Qwen / GLM / Gemini 三类提供方。
- Codex Spark 失败属于**模型可用性与账号限制**，非子孙派生链路问题。
