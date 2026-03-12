# OpenClaw ModelEval-Self：物理执行力与多智能体审计引擎

> **系统定位**：本系统并非传统的“文本问答（Text-in, Text-out）”评测框架，而是针对大语言模型在真实 OS 环境下**“物理状态改变（State-in, State-out）”与“防伪造幻觉”**的深度对抗测试引擎。
> **核心拓扑**：`OPERATOR (主控编排)` -> `sub0 (评审质询)` -> `sub1/sub2 (被测执行体)`

---

## 1) 物理环境与依赖前置 (Prerequisites)

本评测系统深度依赖宿主机的物理沙盒状态。在启动前，必须确认以下环境基线：

1. **核心框架版本**：必须使用 **OpenClaw >= 02.15** 版本。
2. **多智能体权限**：必须在 OpenClaw 的 `openclaw.json` 开启 **孙代Subagent** 能力。
3. **硬编码路径核准**：
   - 检查 Runbook 文件（如 `WORKFLOW-ModelEval-Self-REVIEW.md` 与 `EXEC`）中的 `SESSION_ROOT`（默认为 `/home/ubuntu/.openclaw/agents/main/sessions`）和 `PROJECT_CWD`。
   - **必须**将其全局替换为您本地真实环境的绝对路径。
4. **依赖脚本**：确保项目目录下的 `scripts/transcript_scalpel.py` 存在且具备系统级可执行权限。

---

## 2) 仓库配置与 Git 鉴权准备 (Deployment)

执行体在评测任务（T3）中会进行真实的 Git 提交与推送动作，因此必须配置无阻碍的 Git 鉴权通道。

1. **Fork 隔离**：必须 Fork 本仓库到您的个人账号下，作为子代智能体测试 `git commit/push` 的物理沙盒。
2. **本地克隆**：在 OpenClaw 运行环境的 `PROJECT_CWD` 目录下 `git clone` 您的 Fork 仓库。
3. **静默鉴权 (强约束)**：
   - 必须为 OpenClaw 宿主机的终端配置免密推送权限（配置 SSH Key 或具备写权限的 Github PAT）。
   - 若未配置免密，`sub1` 在执行 `git push` 时将因等待密码输入导致进程死锁挂起。

---

## 3) 一键触发执行协议 (Execution)

系统已被降维为严密的事件驱动状态机。必须通过特定的结构化指令唤醒 OpenClaw 的主会话（OPERATOR）。

请将以下指令直接复制并发送给 OpenClaw 主会话输入框：

### 场景 A：单模型精准测试 (Single Run)
```text
请读取本地目录下的 `WORKFLOW-ModelEval-Self-OPERATOR.md` 文件。
本次评测模式为：单模型精准测试。
目标模型设定为：<填入你的被测模型名，如 claude-3-7-sonnet-20250219>。
请立即基于物理时间生成 Run_ID，并派发 sub0 (Reviewer) 开始执行完整测试流。在 sub0 执行期间，你必须保持挂起并执行同步等待协议。
```

### 场景 B：多模型队列轮询 (Batch Run)
```text
请读取本地目录下的 `WORKFLOW-ModelEval-Self-OPERATOR.md` 文件。
本次评测模式为：多模型串行测试队列。
测试队列清单如下：
1. <模型名称 1>
2. <模型名称 2>
3. <模型名称 3>

请按顺序依次执行。每次循环开始前，必须生成独立的 Run_ID。
在每一轮模型测试期间，派发 sub0 后，你必须严格执行同步锁挂起；等待该模型的轨道 2 验收全部落盘完毕后，方可推进队列，开始测试下一个模型。
```

---

## 4) 终局产物与物理验收 (Artifacts & Audit)

测试结束后，无需询问模型结果，请直接查阅物理文件系统。所有产物均自动落盘至 `Audit-Report/<YYYY-MM-DD>/` 目录下。

* **`review_<Run_ID>_round<X>.md`**：包含核心评分。
    * **轨道 1 (Track 1)**：由 `sub0` 判定的模型执行分数（基于 D1-D5 标准）。
    * **轨道 2 (Track 2)**：位于文件末尾，由 `OPERATOR` 覆写的编排质量与物理证据双重验收结论。若此处为 FAIL，当前模型成绩作废。
* **`raw_logs/` 目录**：存放从 OpenClaw 核心框架抓取的底层 `.jsonl` 母带日志。这是判定模型是否发生“行动幻觉”的绝对物证。
* **`transcript_*.md`**：由脚本生成的人类可读实录副本。

---

## 5) 架构修改与第三方 LLM 评审 (Meta-Management)

**警告：禁止人类手动干预 Runbook 逻辑。**

当前目录下的 `.md` 文件（特别是 `OPERATOR` 与 `REVIEW`）已被重构为高密度的状态机触发器（Triggers）与约束链表。人类视角的散文体修改会破坏 LLM 的执行并发锁。

若需调整评测任务或修改评分权重：
1. 请阅读 `claude-guide.md`（或相关 Meta 提示词文档）。
2. 将需求与现有的 `.md` 源码整体喂给 Claude 3.5 Sonnet / GPT-4o 等高阶推理模型。
3. 声明“维持纯粹的事件驱动链表结构”，由 AI 完成代码级的逻辑增删与正则重构。


---

## 2026-02-16 Legacy vs Recalibrated 评分对比（个人老版评测记录，仅供参考）

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
