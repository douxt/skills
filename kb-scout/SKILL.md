---
name: kb-scout
description: 知识库主动侦察。按 wiki 覆盖领域搜索 YouTube 最新内容，交互式审批后自动下载字幕生成总结。触发：/kb-scout、知识库更新、搜索新视频、scout。
allowed-tools: Read, Write, Bash
---

# /kb-scout — 知识库侦察

定期搜索 YouTube 最新内容 → 交互式审批 → 自动下载字幕并生成中文总结。

## 流程

### 阶段 1：搜索
1. 读 `config/topics.json` 获取搜索领域和关键词
2. 运行 `python3 scripts/scout.py`——yt-dlp 搜索 + 60 天时效过滤 + DB 去重
3. 展示结果表格：标题 | 频道 | 时长 | 发布时间 | 领域

### 阶段 2：审批（交互式）
对每条结果逐条问用户。格式：
```
[1/15] Loop Engineering Just 10x Claude Code
       频道: AI LABS | 时长: 13分 | 发布: 2026-07-09 | 领域: 循环工程
       收录？ [y] 是 [n] 否 [s] 跳过剩余
```
用户答 y 的加入下载队列。

### 阶段 3：下载+总结
对队列中每个视频：
1. yt-dlp 下载字幕（使用项目 .env 的代理配置）
2. 调用 DeepSeek V4 Flash 生成中文结构化总结
3. 写入 /data/docs/<video_id>.md（含 frontmatter）
4. 更新 SQLite DB

全部完成后汇报：成功 N 篇，失败 M 篇，跳过 K 篇。

## 约束
- 使用项目已有 .env 的 PROXY_URL，不硬编码代理
- DB 去重：已有 video_id 自动跳过
- 仅搜索近 60 天发布的视频
- topics.json 可按需编辑，加新领域或调整关键词
