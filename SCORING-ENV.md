# 环境适配层 — Operator 核对清单

> **用途**：列出两个评测体系中的所有环境变量。
> Operator 在首次部署或环境变更时逐项核对并填写实际值。
> **本文件不含评分逻辑**——评分逻辑见 `SCORING-UNIVERSAL.md`。

---

## 1) 远程评估（SG→KR）环境变量

| 变量 | 默认值 / 约定 | Operator 实际值 | 说明 |
|------|--------------|----------------|------|
| KR 机器 SSH 地址 | `ubuntu@3399.work.gd` | ________________ | T1 巡查目标 |
| KR SSH 端口 | `21751` | ________________ | |
| KR SSH 密钥 | `~/.ssh/id_ed25519_seoul` | ________________ | |
| KR nanobot 配置路径 | `~/.nanobot/config.json` | ________________ | 用于读取 RAW_MODEL_STRING |
| KR nanobot session 目录 | `~/.nanobot/sessions/` | ________________ | JSONL 仲裁源 |
| KR workspace 路径 | `~/.nanobot/workspace/` | ________________ | Truth Gate 文件位置 |
| Truth Gate 文件名 | `WORKFLOW-Truth-Gate.md` | ________________ | Round 2 才读 |
| KR 日记 repo | `TheAutomatic/claw_config_kr` | ________________ | T3 push 目标 |
| KR push 分支 | `kr` | ________________ | T3 目标分支 |
| SG 报告目录 | `memory/model-eval/YYYY-MM-DD/` | ________________ | 评审报告存放 |
| CLI 启动命令 | `/home/moss/.local/bin/uv --project ~/nanobot run nanobot agent -s <session_key> -m "<msg>"` | ________________ | KR 侧 CLI 命令模板 |

---

## 2) 自评估（OpenClaw Self-Audit）环境变量

| 变量 | 默认值 / 约定 | Operator 实际值 | 说明 |
|------|--------------|----------------|------|
| SG OpenClaw session 目录 | `/home/ubuntu/.openclaw/agents/main/sessions/` | ________________ | v3 事件流 JSONL |
| T2 写入路径 | `/tmp/openclaw_selfaudit_<run_id>.txt` | ________________ | 临时文件 |
| T3 产物目录 | `Audit-Report/<YYYY-MM-DD>/` | ________________ | git push 的目标目录 |
| T3 push 目标仓库 | `TheAutomatic/OpenModel-Eval-Self.git` | ________________ | |
| T3 push 分支策略 | `Self-audit/<标识>`（如 `Self-audit/Codex_<run_id>`） | ________________ | 并发友好 |
| T4 KR SSH 地址（可选） | `moss@so.3399.work.gd` | ________________ | |
| T4 KR SSH 端口（可选） | `23681` | ________________ | |
| T4 KR SSH 密钥（可选） | `~/.ssh/id_ed25519_seoul_scout` | ________________ | |
| 归档目录 | `Audit-Report/<YYYY-MM-DD>/_sessions/` | ________________ | REVIEW 归档 `.gz` |
| 模型名获取方式 | **Operator 口述**（不从配置文件读取） | ________________ | 与远程评估不同 |
| inspect 脚本路径 | `scripts/inspect_sessions_gz.py` | ________________ | gz 解压+事件流检查 |

---

## 3) 跨体系共享变量

| 变量 | 默认值 / 约定 | Operator 实际值 | 说明 |
|------|--------------|----------------|------|
| run_id 格式 | `YYYYMMDD_HHMM` | ________________ | 重跑=新 run_id |
| 报告命名格式 | `eval_<model_slug>_run<run_id>_round<1\|2>.md` | ________________ | 见 SCORING-MAPPING.md |
| 评分标准版本 | `SCORING-UNIVERSAL.md v1.0` | ________________ | 报告中必须注明 |
| D2 难度系数 | 默认=1.0（不启用） | ________________ | 若要补偿远程评估额外难度，改为 1.2/1.3 |
| 追问次数阈值 | 3+ 仍拿不到证据 → Fail | ________________ | |

---

## 4) 会话日志格式差异

| 属性 | 远程评估（nanobot） | 自评估（OpenClaw） |
|------|-------------------|-------------------|
| 文件格式 | JSONL（每行一个 JSON 对象） | JSONL（每行一个 JSON 对象，v3 事件流） |
| 角色字段路径 | `$.role` | `$.message.role` |
| 工具调用标识 | `$.tools_used`（顶层字段） | `$.message.content[].type == "toolCall"` |
| 时间戳字段 | `$.timestamp`（部分版本可能缺失） | `$.timestamp` |
| 会话标识 | session key（`cli:run<id>:round<N>`） | UUID 文件名 |
| 归档方式 | SG 在 KR 上 `tail` + 直接读取 | REVIEW `gzip -c` 全量归档到 `_sessions/*.gz` |

---

## 版本记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-02-16 | 初版 |
