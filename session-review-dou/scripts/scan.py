#!/usr/bin/env python3
"""session-review-dou 会话扫描器。jq 可选加速，无则回退 Python stdlib。"""
import json, os, sys, glob, subprocess, datetime, urllib.parse

SIGNALS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "signals.json")
LAST_RUN_FILE = "/tmp/session-review-last-run"

def has_jq():
    try:
        subprocess.run(["jq", "--version"], capture_output=True, timeout=2)
        return True
    except: return False

def encode_path(path):
    return urllib.parse.quote(path, safe="")

def discover_project_dir():
    cwd = os.getcwd()
    base = os.path.expanduser(os.environ.get("CLAUDE_CONFIG_DIR", "~/.claude"))
    base = os.path.expanduser(base)
    projects = os.path.join(base, "projects")
    if not os.path.isdir(projects):
        return None
    encoded = encode_path(cwd)
    for variant in (encoded, "-" + cwd.lstrip("/").replace("/", "-")):
        candidate = os.path.join(projects, variant)
        if os.path.isdir(candidate):
            return candidate
    return None

def get_since():
    if os.path.exists(LAST_RUN_FILE):
        with open(LAST_RUN_FILE) as f:
            return f.read().strip()
    return (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d")

def update_last_run():
    with open(LAST_RUN_FILE, "w") as f:
        f.write(datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))

def load_signals():
    with open(SIGNALS_FILE) as f:
        return json.load(f)

def detect_signals(text, signals):
    markers = []
    tl = text.lower()
    for pat in signals.get("corrections_cn", []):
        if pat in text:
            markers.append(f"correction:{pat}")
            break
    for pat in signals.get("corrections_en", []):
        if pat.lower() in tl:
            markers.append(f"correction:{pat}")
            break
    for pat in signals.get("completion_claims", []):
        if pat.lower() in tl:
            markers.append(f"claim:{pat}")
            break
    return markers

def extract_text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(
            b.get("text", "").strip()
            for b in content
            if isinstance(b, dict) and b.get("type") == "text" and b.get("text", "").strip()
        )
    return ""

def summarize_session(filepath, signals):
    try:
        fname = os.path.basename(filepath)
        sid = fname.replace(".jsonl", "")
        size_kb = os.path.getsize(filepath) // 1024
        timestamp = ""
        user_msgs, assistant_summaries, all_markers = [], [], set()
        line_count, total_text_len = 0, 0
        with open(filepath) as f:
            for line in f:
                line_count += 1
                try: o = json.loads(line)
                except: continue
                t = o.get("type", "")
                if t not in ("user", "assistant"):
                    continue
                if not timestamp:
                    timestamp = o.get("timestamp", "")[:19]
                text = extract_text(o.get("message", {}).get("content", ""))
                if not text: continue
                if t == "user":
                    total_text_len += len(text)
                    m = detect_signals(text, signals)
                    all_markers.update(m)
                    user_msgs.append({"text": text[:200], "len": len(text), "markers": m})
                elif t == "assistant":
                    total_text_len += min(len(text), 500)
                    assistant_summaries.append(text[:150])
                    all_markers.update(detect_signals(text, signals))
        topic = user_msgs[0]["text"][:80] if user_msgs else "(无用户消息)"
        return {
            "session_id": sid, "timestamp": timestamp, "size_kb": size_kb,
            "lines": line_count, "user_msg_count": len(user_msgs),
            "topic": topic, "markers": list(all_markers),
            "user_sample": user_msgs[:5], "assistant_sample": assistant_summaries[:3]
        }
    except Exception as e:
        return {"session_id": fname, "error": str(e)}

def list_sessions():
    project_dir = discover_project_dir()
    if not project_dir:
        print("未找到当前项目的会话目录。")
        print(f"   CWD: {os.getcwd()}")
        return
    signals = load_signals()
    since = get_since()
    jsonl_files = sorted(
        [f for f in glob.glob(os.path.join(project_dir, "*.jsonl"))
         if "/subagents/" not in f],
        key=os.path.getmtime, reverse=True
    )
    if not jsonl_files:
        print("当前项目未找到历史会话。")
        print("常见原因：会话在其他机器上。")
        print("解决方案：")
        print("  1) 从其他机器复制 ~/.claude/projects/<项目编码>/ 目录")
        print("  2) 运行 scan.py 后复制摘要文件")
        print("  3) 设 CLAUDE_CONFIG_DIR 环境变量指向共享存储")
        return
    print(f"{len(jsonl_files)} 个会话 ({project_dir})")
    print(f"增量：只展示 {since} 之后\n")
    print(f"{'#':>3}  {'会话ID':<38} {'时间':<20} {'大小':>6} {'消息':>5}  主题")
    print("-" * 100)
    for i, fp in enumerate(jsonl_files):
        s = summarize_session(fp, signals)
        if "error" in s: continue
        if s["timestamp"] and s["timestamp"] < since: continue
        print(f"{i+1:>3}  {s['session_id'][:36]:<38} {s['timestamp']:<20} {s['size_kb']:>5}K {s['user_msg_count']:>4}u  {s['topic'][:60]}")
    # last-run 不在此更新——由 SKILL.md 阶段 1 确认用户选择后再更新
    print("\n输入 /session-review-dou <编号> 选择会话，如 /session-review-dou 1 3")

if __name__ == "__main__":
    if "--list" in sys.argv:
        list_sessions()
    elif "--summarize" in sys.argv:
        idx = sys.argv.index("--summarize")
        sid = sys.argv[idx+1] if idx+1 < len(sys.argv) else None
        if sid:
            project_dir = discover_project_dir()
            if project_dir:
                fp = os.path.join(project_dir, f"{sid}.jsonl")
                if os.path.exists(fp):
                    print(json.dumps(summarize_session(fp, load_signals()), ensure_ascii=False, indent=2))
                else:
                    print(json.dumps({"error": f"会话 {sid} 不存在"}, ensure_ascii=False))
    else:
        print("用法: scan.py --list  |  scan.py --summarize <session-id>")
        if not has_jq():
            print("提示: jq 未安装，已使用 Python stdlib。安装 jq 可加速: brew install jq / apt install jq")
