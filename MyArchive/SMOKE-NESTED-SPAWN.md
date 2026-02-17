# SMOKE-NESTED-SPAWN (3分钟回归)

## 目的
快速验证链路是否可用：
`主会话 -> reviewer 子代理 -> 两个孙代 (R1/R2)`。

> 这是链路健康检查，不是完整评测。

---

## 触发时机
- 每次修改 runbook / 编排模板后立即执行 1 次。
- 每次修改 subagent 相关配置（`maxSpawnDepth` / `maxChildrenPerAgent` / tools allowlist）后执行 1 次。

---

## 固定检查项（必须全过）

### S1. Spawn 能力
- reviewer 子代理能成功派出 2 个孙代：`exec-r1` 与 `exec-r2`。
- 记录两个孙代 `session_key`。

### S2. 会话隔离
- `exec-r1` 与 `exec-r2` 的 `session_key` 必须不同。
- 任一孙代不得声称执行另一轮任务。

### S3. 最小执行证据
- 每个孙代至少完成：
  - 1 次工具调用（例如 `exec`）
  - 1 个可核验文件产物

### S4. 回传完整性
- reviewer 能收齐两路结果并形成统一汇总。
- 不允许“只收到一轮”却标记成功。

### S5. 路径正确性
- 产物必须落在：
  `/home/ubuntu/.openclaw/workspace/projects/OpenModel-Eval-Self-repo/`
- 若落到 workspace 根仓库（`/home/ubuntu/.openclaw/workspace/`）则判定 FAIL。

### S6. 失败可诊断
- 若失败，必须输出原始错误文本（如 `Tool sessions_spawn not found`），不能静默失败。

---

## 快速执行模板（建议）
1) 由主会话 spawn 一个 reviewer 子代理。
2) reviewer 内部再 spawn 两个孙代：
   - `smoke-grandchild-r1`
   - `smoke-grandchild-r2`
3) 两个孙代分别写入：
   - `.../smoke_nested_spawn/<RUN_ID>/r1.txt`
   - `.../smoke_nested_spawn/<RUN_ID>/r2.txt`
4) reviewer 回传：
   - nested_spawn_status
   - grandchild_session_keys
   - artifact_paths
   - verdict(PASS/FAIL)

---

## 判定
- **PASS**：S1~S6 全部满足。
- **FAIL**：任一项不满足。

---

## 输出格式（建议）
- run_id:
- nested_spawn_status:
- grandchild_session_keys:
- artifacts:
- checks:
  - S1: PASS/FAIL
  - S2: PASS/FAIL
  - S3: PASS/FAIL
  - S4: PASS/FAIL
  - S5: PASS/FAIL
  - S6: PASS/FAIL
- final_verdict: PASS/FAIL
- raw_error: NONE / <exact text>
