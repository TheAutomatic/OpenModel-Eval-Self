import json
import os
import argparse

def parse_session(path):
    transcript = []
    if not os.path.exists(path):
        return f"File not found: {path}"
    
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line)
                if data.get('type') != 'message':
                    continue
                
                msg = data.get('message', {})
                role = msg.get('role', 'unknown')
                content_list = msg.get('content', [])
                
                transcript.append(f"### [{role.upper()}]")
                
                for item in content_list:
                    if isinstance(item, str):
                        transcript.append(item)
                    elif isinstance(item, dict):
                        if item.get('type') == 'text':
                            transcript.append(item.get('text', ''))
                        elif item.get('type') == 'toolCall':
                            transcript.append(f"🛠️ **CALL TOOL**: `{item.get('name')}`")
                            args = item.get('arguments', {})
                            transcript.append(f"```json\n{json.dumps(args, indent=2, ensure_ascii=False)}\n```")
                        elif item.get('type') == 'toolResult':
                            transcript.append(f"✅ **TOOL RESULT**:")
                            # Handle potential JSON strings in content for better readability
                            res_content = item.get('content', '')
                            transcript.append(f"```text\n{res_content}\n```")
                transcript.append("\n---\n")
            except Exception as e:
                transcript.append(f"Error parsing line: {e}")
    return "\n".join(transcript)

def main():
    parser = argparse.ArgumentParser(description="Convert OpenClaw JSONL session logs to readable Markdown.")
    parser.add_argument("input", help="Input JSONL file path")
    parser.add_argument("-o", "--output", help="Output Markdown file path (default: input with .md extension)")
    parser.add_argument("--title", help="Title for the transcript", default="OpenClaw Session Transcript")

    args = parser.parse_args()
    
    if not args.output:
        args.output = os.path.splitext(args.input)[0] + ".md"

    print(f"Processing: {args.input} -> {args.output}")
    content = parse_session(args.input)
    
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(f"# {args.title}\n\n")
        f.write(content)
    
    print("Success!")

if __name__ == "__main__":
    main()
