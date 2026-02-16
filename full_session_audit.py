"""
Full session event-stream audit for 5 target runs.
Decompresses all .gz archives, parses JSONL, extracts:
- assistant turn count
- toolCall / toolResult counts per turn
- git commit / git push grep hits
- content length per assistant turn
- any anomalies (tools present but no content, or content but no tools)
"""
import gzip, json, glob, os, sys

SESSION_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                           "Audit-Report", "2026-02-16", "_sessions")

TARGET_RUNS = ["1607", "1610", "1636", "1639", "0858"]

def analyze_session(path):
    """Analyze a single .gz session file."""
    results = {
        "file": os.path.basename(path),
        "total_lines": 0,
        "message_lines": 0,
        "assistant_turns": [],
        "git_commit_hits": [],
        "git_push_hits": [],
        "tool_call_total": 0,
        "tool_result_total": 0,
        "anomalies": [],
    }
    
    try:
        with gzip.open(path, 'rt', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                results["total_lines"] = i
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    results["anomalies"].append(f"L{i}: JSON parse error")
                    continue
                
                # Check event type
                evt_type = d.get("type", "")
                
                # Handle v3 event-stream format (type=message wrapping)
                msg = None
                if evt_type == "message":
                    msg = d.get("message", {})
                elif d.get("role"):
                    # Direct message format (no type wrapper)
                    msg = d
                else:
                    continue  # skip non-message events
                
                if not msg:
                    continue
                
                results["message_lines"] += 1
                role = msg.get("role", "")
                
                if role != "assistant":
                    continue
                
                # Analyze assistant turn
                content = msg.get("content", "")
                tools_used = msg.get("tools_used")
                
                # Count toolCall/toolResult in content array (v3 format)
                tc_count = 0
                tr_count = 0
                content_text = ""
                
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict):
                            btype = block.get("type", "")
                            if btype == "toolCall":
                                tc_count += 1
                            elif btype == "toolResult":
                                tr_count += 1
                            elif btype == "text":
                                content_text += block.get("text", "")
                        elif isinstance(block, str):
                            content_text += block
                elif isinstance(content, str):
                    content_text = content
                
                clen = len(content_text)
                
                turn_info = {
                    "line": i,
                    "clen": clen,
                    "tools_used": tools_used,
                    "toolCall_count": tc_count,
                    "toolResult_count": tr_count,
                }
                results["assistant_turns"].append(turn_info)
                results["tool_call_total"] += tc_count
                results["tool_result_total"] += tr_count
                
                # Grep for git commit / git push in full line text
                line_lower = line.lower()
                if "git commit" in line_lower:
                    results["git_commit_hits"].append(f"L{i}")
                if "git push" in line_lower:
                    results["git_push_hits"].append(f"L{i}")
                
                # Anomaly detection
                has_tools = (tools_used is not None and tools_used != []) or tc_count > 0
                if has_tools and clen < 50:
                    turn_info["anomaly"] = "PARTIAL-SILENT: tools present but content < 50 chars"
                    results["anomalies"].append(f"L{i}: {turn_info['anomaly']}")
                if not has_tools and clen > 200 and tools_used is None and tc_count == 0:
                    # Check if content looks like terminal output
                    if any(kw in content_text for kw in ["rc=", "ubuntu@", "root@", "$ ", "# "]):
                        turn_info["anomaly"] = "SUSPECT-FAKE: no tools but content has terminal markers"
                        results["anomalies"].append(f"L{i}: {turn_info['anomaly']}")
    
    except Exception as e:
        results["anomalies"].append(f"FILE ERROR: {e}")
    
    return results

def print_report(results):
    """Print analysis for one session file."""
    print(f"\n{'='*80}")
    print(f"FILE: {results['file']}")
    print(f"  Total lines: {results['total_lines']}")
    print(f"  Message lines: {results['message_lines']}")
    print(f"  Assistant turns: {len(results['assistant_turns'])}")
    print(f"  toolCall total: {results['tool_call_total']}")
    print(f"  toolResult total: {results['tool_result_total']}")
    print(f"  git commit hits: {results['git_commit_hits'] or 'NONE'}")
    print(f"  git push hits: {results['git_push_hits'] or 'NONE'}")
    
    if results['anomalies']:
        print(f"  ANOMALIES:")
        for a in results['anomalies']:
            print(f"    - {a}")
    
    print(f"  --- Assistant Turn Details ---")
    for t in results['assistant_turns']:
        flag = ""
        if t.get("anomaly"):
            flag = f" *** {t['anomaly']} ***"
        tools_info = ""
        if t.get("tools_used") is not None:
            tools_info = f" tools_used={t['tools_used']}"
        if t["toolCall_count"] > 0 or t["toolResult_count"] > 0:
            tools_info += f" tc={t['toolCall_count']} tr={t['toolResult_count']}"
        print(f"    L{t['line']} | clen={t['clen']}{tools_info}{flag}")

def main():
    print(f"Session directory: {SESSION_DIR}")
    print(f"Target runs: {TARGET_RUNS}")
    
    all_files = sorted(glob.glob(os.path.join(SESSION_DIR, "*.gz")))
    target_files = []
    for f in all_files:
        bn = os.path.basename(f)
        for run_id in TARGET_RUNS:
            if f"_{run_id}_" in bn:
                target_files.append(f)
                break
    
    print(f"\nFound {len(target_files)} session files for target runs:")
    for f in target_files:
        print(f"  {os.path.basename(f)} ({os.path.getsize(f)} bytes)")
    
    all_results = []
    for f in target_files:
        r = analyze_session(f)
        all_results.append(r)
        print_report(r)
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    for r in all_results:
        commit = "YES" if r["git_commit_hits"] else "NO"
        push = "YES" if r["git_push_hits"] else "NO"
        anomaly_count = len(r["anomalies"])
        print(f"  {r['file'][:60]:60s} | turns={len(r['assistant_turns']):3d} | tc={r['tool_call_total']:3d} | commit={commit:3s} | push={push:3s} | anomalies={anomaly_count}")

if __name__ == "__main__":
    main()
