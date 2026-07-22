---
name: session-review-dou
description: 会话尸检（Session Autopsy）。对项目历史会话执行系统性尸检，六维诊断错误模式与最佳实践升级机会，输出带原文证据的改进建议。触发：/session-review-dou、回顾会话、分析历史会话、诊断错误。
allowed-tools: Read, Write, Bash
---

# /session-review-dou — 会话尸检

扫描 Claude Code 历史会话 → 六维诊断 + root cause 分析 → Turn-based→Proactive 升级路径。

## 硬约束（不可跳过）

1. 累积阈值：同一发现 ≥3 个不同会话 AND 跨 ≥2 个日历日 → 永久规则。1-2 次仅标记关注。
2. 先去重：生成建议前先读 CLAUDE.md + memory/MEMORY.md。已覆盖的只更新 xN 计数器（不重复写）。
3. 干净即空：无问题时输出"✅ 无可写规则"。即使空报告也写入 reviews/ 归档（供闭环对比）。
4. 单次最多 3 个会话。超出时提示分批。

## 阶段 1：扫描会话

1. 检测 jq 是否可用（`command -v jq`）。无则提示。
2. 运行 `python3 scripts/scan.py --list` 展示会话列表（已分析的打 ✅）
3. 让用户选择至多 3 个会话。若选中已分析的会话，提示"该会话已于 YYYY-MM-DD 分析过，重新分析将覆盖旧报告。继续？"
4. 对选中的每个会话运行 `python3 scripts/scan.py --summarize <id>`，生成压缩摘要
5. 展示摘要概览，确认后进入阶段 2

阶段 1 完成后：Read `steps/phase-2.md` 获取诊断指令。**阶段 1 确认前不得预读后续阶段。**

（阶段 1 结束。完成后加载 steps/phase-2.md）
