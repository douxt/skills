#!/usr/bin/env python3
"""Stop Hook: 会话结束时提醒用户回顾。"""
import os, sys

# 子代理静默退出
if os.environ.get("CLAUDE_CODE_SUBAGENT"):
    sys.exit(0)

print("💡 会话结束。运行 /session-review-dou 回顾本次会话并提取改进点。")
