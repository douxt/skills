# kb-scout

知识库主动侦察。按 wiki 覆盖领域搜索 YouTube 最新内容，交互式审批后自动下载字幕生成总结。

## 领域覆盖

| 领域 | 搜索内容 |
|------|---------|
| Claude Code 工作流 | /goal /loop 实战教程 |
| AI Agent 架构 | 子代理模式、多代理编排 |
| Skill 工程 | 技能设计最佳实践 |
| 循环工程 | 自主循环工作流 |
| Token 优化 | 降本方案、上下文压缩 |
| 知识库/RAG | Karpathy wiki、RAG 架构 |
| Harness Engineering | 钩子系统、MCP 集成 |
| 深度研究 | STORM 方法论、多视角研究 |

## 安装

```bash
npx skills add douxt/skills -g -a claude-code -y
```

## 使用

```bash
/kb-scout          # 搜索 → 审批 → 下载
```

### 自定义搜索领域

编辑 `config/topics.json`，按模板加新领域：

```json
{"name": "新领域名", "queries": ["搜索词1", "搜索词2"], "max_per_query": 3}
```

## 前置条件

- 项目有 `.env` 文件含 `PROXY_URL`
- 项目有 SQLite DB (`/data/youtube-kb.db` 或 `data/youtube-kb.db`)
- yt-dlp 已安装
