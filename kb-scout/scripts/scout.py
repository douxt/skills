#!/usr/bin/env python3
"""kb-scout: YouTube 搜索 + 时效过滤 + DB 去重。"""
import json, os, sys, sqlite3, subprocess, datetime, tempfile

SKILL_DIR = os.path.dirname(os.path.dirname(__file__))
TOPICS_FILE = os.path.join(SKILL_DIR, "config", "topics.json")
OUTPUT_FILE = "/tmp/kb-scout-results.json"

def load_env():
    """读项目 .env 取 PROXY_URL"""
    for p in [".env", os.path.join(os.path.dirname(os.getcwd()), ".env")]:
        fp = os.path.join(os.getcwd(), p)
        if os.path.exists(fp):
            with open(fp) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("PROXY_URL="):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None

def get_existing_videos():
    """从 SQLite DB 取已有 video_id 列表（去重用）"""
    db_paths = ["/data/youtube-kb.db", os.path.join(os.getcwd(), "data/youtube-kb.db")]
    for dbp in db_paths:
        if os.path.exists(dbp):
            conn = sqlite3.connect(dbp)
            ids = set(row[0] for row in conn.execute("SELECT video_id FROM videos").fetchall())
            conn.close()
            return ids
    return set()

def search_youtube(query, max_results, proxy_url, max_age_days):
    """yt-dlp 搜索 YouTube，返回结果列表"""
    from datetime import timedelta
    cutoff = (datetime.datetime.now() - timedelta(days=max_age_days)).strftime("%Y%m%d")
    cmd = [
        "yt-dlp",
        f"ytsearch{max_results}:{query}",
        "--dump-json", "--no-playlist", "--flat-playlist",
        "--dateafter", cutoff
    ]
    env = os.environ.copy()
    if proxy_url:
        cmd.insert(1, proxy_url)
        cmd.insert(1, "--proxy")
    results = []
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120, env=env)
        for line in proc.stdout.strip().split("\n"):
            if not line: continue
            try:
                d = json.loads(line)
                results.append({
                    "video_id": d.get("id", ""),
                    "title": d.get("title", ""),
                    "channel": d.get("channel", "") or d.get("uploader", ""),
                    "duration": d.get("duration", 0) or 0,
                    "upload_date": d.get("upload_date", ""),
                    "url": d.get("webpage_url", ""),
                    "description": (d.get("description", "") or "")[:200]
                })
            except json.JSONDecodeError:
                continue
    except Exception as e:
        print(f"搜索失败 [{query}]: {e}", file=sys.stderr)
    return results

def main():
    with open(TOPICS_FILE) as f:
        config = json.load(f)
    proxy = load_env()
    existing = get_existing_videos()
    max_age = config["max_age_days"]
    all_results = []
    seen = set()

    for topic in config["topics"]:
        for query in topic["queries"]:
            results = search_youtube(query, topic["max_per_query"], proxy, max_age)
            for r in results:
                vid = r["video_id"]
                if vid in existing or vid in seen:
                    continue
                seen.add(vid)
                r["topic"] = topic["name"]
                all_results.append(r)

    all_results.sort(key=lambda x: x["upload_date"], reverse=True)
    all_results = all_results[:config["max_total_results"]]

    with open(OUTPUT_FILE, "w") as f:
        json.dump({"results": all_results, "existing_count": len(existing), "total_found": len(all_results)}, f, ensure_ascii=False, indent=2)

    print(f"搜索完成：{len(all_results)} 条新结果（已排除 {len(existing)} 条已有视频）")
    print(f"结果已写入 {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
