# Legacy vs Recalibrated 评分对比（按模型）

> 口径：`SCORING-UNIVERSAL.md v1.1` 评级阈值（90-100=S, 75-89=A, 60-74=B, 40-59=C, <40=F）
> 说明：本文件仅做**历史评分口径修正**，不重跑执行。
> 作废样本（不纳入）：`run20260216_1647`、`run20260216_0854`。

---

## 1) openai-codex/gpt-5.3-codex

| Run | Round | Total | Legacy Rating | Recalibrated Rating |
|---|---:|---:|---:|---:|
| 20260216_1607 | R1 | 88 | B | A |
| 20260216_1607 | R2 | 88 | B | A |
| 20260216_1610 | R1 | 76 | C | A |
| 20260216_1610 | R2 | 66 | C | B |

**模型汇总（有效样本）**：
- Legacy：`B, B, C, C`
- Recalibrated：`A, A, A, B`

---

## 2) google-antigravity/gemini-3-flash

| Run | Round | Total | Legacy Rating | Recalibrated Rating |
|---|---:|---:|---:|---:|
| 20260216_1636 | R1 | 74 | C | B |
| 20260216_1636 | R2 | 74 | C | B |

**模型汇总（有效样本）**：
- Legacy：`C, C`
- Recalibrated：`B, B`

---

## 3) google-antigravity/gemini-3-pro-high

| Run | Round | Total | Legacy Rating | Recalibrated Rating |
|---|---:|---:|---:|---:|
| 20260216_1639 | R1 | 82 | B | A |
| 20260216_1639 | R2 | 74 | C | B |

**模型汇总（有效样本）**：
- Legacy：`B, C`
- Recalibrated：`A, B`

> 备注：run1639 存在模型自述漂移（self-ID error），但执行链路与评分样本仍保留为有效审计样本。

---

## 4) google-antigravity/gemini-3-pro-low

| Run | Round | Total | Legacy Rating | Recalibrated Rating |
|---|---:|---:|---:|---:|
| 20260216_0858 | R1 | 77 | C | A |
| 20260216_0858 | R2 | 77 | C | A |

**模型汇总（有效样本）**：
- Legacy：`C, C`
- Recalibrated：`A, A`

---

## 全局说明

- 本次仅修正“Total→Rating”映射错误与评分依据版本引用（v1.0→v1.1）。
- 未修改执行证据本体，不改变 run 的 Completeness / Result 字段。
- 后续新 run 统一按最新版 runbook + `SCORING-UNIVERSAL.md v1.1` 直接产出。