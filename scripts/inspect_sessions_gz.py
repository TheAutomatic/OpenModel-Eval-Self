#!/usr/bin/env python3
"""
inspect_sessions_gz.py — 解压并摘要 _sessions/*.gz 中的 v3 事件流

用法：
  python3 scripts/inspect_sessions_gz.py Audit-Report/2026-02-16/_sessions
  python3 scripts/inspect_sessions_gz.py Audit-Report/2026-02-16/_sessions --anchor 2026-02-16T03:10:38Z
  python3 scripts/inspect_sessions_gz.py Audit-Report/2026-02-16/_sessions --grep "git commit"
  python3 scripts/inspect_sessions_gz.py Audit-Report/2026-02-16/_sessions --grep "git push" --context 200

输出格式（每个 assistant 回合一行）：
  L<行号> | ts=<时间戳> | tC=<toolCall数> tR=<toolResult数> | cLen=<content JSON 长度> [| MATCH: <匹配片段>]

选项：
  --anchor <UTC>    只显示该时间点之后的事件（用于按 Round 切片）
  --grep <pattern>  在 toolCall 的 command/arguments 中搜索关键词（如 "git commit"）
  --context <N>     --grep 命中时，展示命中行周围的 N 字符上下文（默认 120）
  --full            不做摘要，输出每行完整 JSON（用于深挖单条事件）
"""

import gzip, json, glob, sys, os, argparse
from datetime import datetime


def parse_ts(ts_str):
    """尽力解析 ISO 时间戳"""
    if not ts_str or ts_str == "N/A":
        return None
    try:
        # strip trailing Z and fractional seconds for simplicity
        clean = ts_str.rstrip("Z").split(".")[0]
        return datetime.fromisoformat(clean)
    except Exception:
        return None


def count_tools(msg):
    """统计 v3 事件流中一个 message 的 toolCall / toolResult 数量"""
    c = msg.get("content")
    if not isinstance(c, list):
        return 0, 0
    tc = sum(1 for x in c if isinstance(x, dict) and x.get("type") == "toolCall")
    tr = sum(1 for x in c if isinstance(x, dict) and x.get("type") == "toolResult")
    return tc, tr


def extract_tool_commands(msg):
    """提取所有 toolCall 中的 command / arguments 文本"""
    c = msg.get("content")
    if not isinstance(c, list):
        return []
    cmds = []
    for x in c:
        if not isinstance(x, dict) or x.get("type") != "toolCall":
            continue
        args = x.get("arguments") or {}
        # exec 工具通常有 command 字段
        cmd = args.get("command", "")
        if cmd:
            cmds.append(cmd)
        else:
            # 其他工具：序列化整个 arguments
            cmds.append(json.dumps(args, ensure_ascii=False)[:300])
    return cmds


def inspect_gz(gz_path, anchor_dt=None, grep_pattern=None, context_len=120, full_mode=False):
    """解压并解析一个 .gz 文件，返回格式化行列表"""
    results = []
    with gzip.open(gz_path, "rt", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            try:
                d = json.loads(line)
            except Exception:
                continue
            if d.get("type") != "message":
                continue
            m = d.get("message") or {}
            if m.get("role") != "assistant":
                continue

            ts = d.get("timestamp", "N/A")

            # 锚点过滤
            if anchor_dt:
                evt_dt = parse_ts(ts)
                if evt_dt and evt_dt < anchor_dt:
                    continue

            tc, tr = count_tools(m)
            content = m.get("content", [])
            clen = len(json.dumps(content, ensure_ascii=False)) if content else 0

            summary = f"  L{i} | ts={ts} | tC={tc} tR={tr} | cLen={clen}"

            # grep 筛选
            if grep_pattern:
                cmds = extract_tool_commands(m)
                matched = [c for c in cmds if grep_pattern.lower() in c.lower()]
                if not matched:
                    continue
                for mc in matched:
                    # 截取匹配上下文
                    idx = mc.lower().find(grep_pattern.lower())
                    start = max(0, idx - context_len // 2)
                    end = min(len(mc), idx + len(grep_pattern) + context_len // 2)
                    snippet = mc[start:end].replace("\n", "\\n")
                    summary += f" | MATCH: ...{snippet}..."

            if full_mode:
                summary += f"\n    FULL: {json.dumps(d, ensure_ascii=False)[:2000]}"

            results.append(summary)
    return results


def main():
    parser = argparse.ArgumentParser(description="Inspect OpenClaw session .gz archives")
    parser.add_argument("session_dir", help="Path to _sessions/ directory containing .gz files")
    parser.add_argument("--anchor", help="Only show events after this UTC timestamp (e.g. 2026-02-16T03:10:38Z)")
    parser.add_argument("--grep", help="Search for pattern in toolCall commands/arguments")
    parser.add_argument("--context", type=int, default=120, help="Characters of context around grep match (default 120)")
    parser.add_argument("--full", action="store_true", help="Show full JSON for each matching event")
    args = parser.parse_args()

    anchor_dt = None
    if args.anchor:
        anchor_dt = parse_ts(args.anchor)
        if not anchor_dt:
            print(f"WARNING: could not parse anchor timestamp: {args.anchor}", file=sys.stderr)

    gz_files = sorted(glob.glob(os.path.join(args.session_dir, "*.gz")))
    if not gz_files:
        print(f"No .gz files found in {args.session_dir}")
        sys.exit(1)

    for gz_path in gz_files:
        bn = os.path.basename(gz_path)
        print(f"\n=== {bn} ===")
        results = inspect_gz(gz_path, anchor_dt, args.grep, args.context, args.full)
        if results:
            for r in results:
                print(r)
        else:
            filter_desc = []
            if anchor_dt:
                filter_desc.append(f"anchor={args.anchor}")
            if args.grep:
                filter_desc.append(f"grep={args.grep}")
            print(f"  (no matching assistant events{' with ' + ', '.join(filter_desc) if filter_desc else ''})")


if __name__ == "__main__":
    main()
