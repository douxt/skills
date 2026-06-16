---
name: review-cc-cli
description: Use when needing an independent code review of current changes before committing or merging
allowedTools: Read,Grep,Glob,Bash
license: MIT
---

# /review

## 安装

```
# 1. 将 skill 放到 ~/.claude/skills/
cp -r review-cc-cli ~/.claude/skills/review-cc-cli

# 2. 部署配置 + rubrics
cd ~/.claude/skills/review-cc-cli && bash scripts/install.sh
```

之后在任意项目中执行 `/review` 即可。

在当前对话中启动一个**独立上下文**的 `claude -p` 实例，只读评审代码/计划/测试。
多轮评审**复用同一 session**，第 2 轮起利用 prompt cache 大幅降本。

## 评审范围指定

`/review` 支持灵活指定评审内容：

| 用法 | 评审范围 | 示例 |
|------|----------|------|
| `/review` | 未提交的代码改动（默认） | `/review` |
| `/review <文件>` | 指定文件（代码/文档/计划） | `/review plan.md` |
| `/review <目录>` | 指定目录下全部文件 | `/review src/utils/` |
| `/review <git范围>` | git 历史改动 | `/review HEAD~3`、`/review main..feature` |
| `/review <计划文件>` | 只评审计划文档本身 | `/review docs/plan.md` |
| `/review <计划文件> +` | 实施对照评审 | `/review plan.md +` |
| `/review --shallow` | 聚焦审查，不额外探索代码库 | `/review --shallow src/` |
| `/review --deep` | 允许审查者读相关文件深入了解上下文 | `/review --deep src/foo.js` |
| `/review --fast` | 用便宜模型快速评审（默认） | `/review --fast src/` |
| `/review --model <ID>` | 指定任意模型 | `/review --model gpt-4o src/` |
| `/review --rubric <名称>` | 指定评审标准文件 | `/review --rubric security src/auth/` |

### 模型映射

子进程 `claude -p` 默认使用系统的当前模型。先读 `~/.claude/settings.json` 获取自定义模型 ID，没有再回退：

| 参数 | 读取配置键 | 回退 | 适用 |
|------|-----------|------|------|
| `--fast`（默认）| `ANTHROPIC_DEFAULT_HAIKU_MODEL` | `ANTHROPIC_MODEL` → 不传 | 快速审查，最省 |
| `--medium` | `ANTHROPIC_DEFAULT_SONNET_MODEL` | `ANTHROPIC_MODEL` → 不传 | 平衡质量和成本 |
| `--deep` | `ANTHROPIC_DEFAULT_OPUS_MODEL` | `ANTHROPIC_MODEL` → 不传 | 深度审查，最强 |
| `--model <原始ID>` | 直接传递 | — | 自定义任意模型 |

模型参数与上下文参数（`--shallow`/`--deep`）独立。默认 `--fast`。

## Rubric 自动匹配

评审标准按场景拆分到 `~/.claude/review-rubrics/` 目录。当不指定 `--rubric` 时，根据文件路径自动匹配：

| 路径特征 | 自动匹配 rubric |
|----------|---------------|
| `auth/`、`login`、`password`、`token`、`session` | default + security |
| `test/`、`spec/`、`*.test.*`、`*_test.*` | default + testing |
| `*.md`、`plan`、`方案`、`docs/` | default + plan |
| `*.yml`、`*.yaml`、`.github/`、`Dockerfile`、`compose` | default + config |
| `benchmark`、`perf`、`慢查询`、大量循环 | default + performance |
| 以上都不匹配 | default |

优先级：显式 `--rubric` > 路径自动匹配 > 默认 default。

合并多个 rubric：`--rubric config,testing`

计划也可直接在对话中提供，不需要落文件。主实例把讨论要点塞入子进程 prompt 即可。

### 上下文控制

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| 默认 | 审查指定文件，可读明显相关的文件 | 常规代码评审 |
| `--shallow` | 只看 diff 内容 | 格式检查、小改动 |
| `--deep` | 可 grep 项目结构、读相关模块 | 跨模块改动、架构评审 |

## 专用 settings 文件

`~/.claude/settings-review.json` 为子进程授权：
- Read 所有项目文件
- Write `.review-*`（评审报告 + 会话状态文件，写到项目根目录）
- 拒绝写密钥类文件

## 流程

```
你 → /review [范围]
      ↓
主实例（当前对话）:
  ① 确定评审范围
  ② git diff --stat 确认变更集
  ③ Bash: claude -p [--model <模型ID>] --permission-mode auto \
          --settings ~/.claude/settings-review.json --output-format json
          （首次创建新 session；后续 --resume <session_id> 重用）
      ↓
步骤 ④ 构造子进程 prompt：
  要求子进程：
    - Read 要评审的文件
    - Read ~/.claude/review-rubrics/{rubric}.md 获取评审标准
    - Write 评审报告到 `.review-report-<slug>.json`（项目根目录，自动匹配 `Write(.review-*)` 规则）
    - 输出 JSON 格式结果
      ↓
子实例执行评审，写入 `.review-report-<slug>.json`（项目根目录）
      ↓
主实例:
  ⑤ 从 JSON 结果中提取 session_id 和 result
  ⑥ 写会话文件：
      文件名：.review-session-${CLAUDE_CODE_SESSION_ID}
      内容：{"sessionId":"<子进程 session_id>","round":<N>,"maxRounds":3}
     （若 round ≥ maxRounds，删除会话文件）
  ⑦ 展示评审报告
```

## 子进程输出格式

主实例解析子进程的 JSON 输出时，子进程 prompt 必须要求以下 JSON 结构：

```json
{
  "verdict": "APPROVED | CHANGES_REQUESTED | BLOCKED",
  "round": 1,
  "summary": "总体评价",
  "criticalIssues": [
    {"file": "路径", "line": 行号, "severity": "high|medium|low", "desc": "问题描述"}
  ],
  "suggestions": ["改进建议"],
  "planChecks": [
    {"requirement": "计划要求", "status": "implemented|partial|missing", "detail": "说明"}
  ]
}
```

主实例从 `result` 字段的文本中提取上述 JSON 块，解析 verdict 和 nextStep。

## 错误处理

子进程 `claude -p` 可能失败，定义以下降级策略：

| 场景 | 处理 |
|------|------|
| `claude` 命令不存在 | 告知用户，降级为当前对话内直接评审 |
| 子进程超时（>60s） | 重试一次，再失败则提示用户手动检查 |
| 输出无有效 JSON 块 | 把原始文本当评审报告展示 |

## 多轮会话复用

- `.review-session-<SESSION_ID>` 存储 `{"sessionId": "abc123", "round": 1, "maxRounds": 3}`
  - `<SESSION_ID>` 从环境变量 `CLAUDE_CODE_SESSION_ID` 获取，每个会话独立
  - 主实例在步骤 ⑤-⑥ 负责读写此文件
  - 并发会话各自读写自己的文件，不冲突
- 首次 `/review` → round=1，创建 session，写 `.review-session-<SESSION_ID>`
- 后续 `/review` → 读 `.review-session-<SESSION_ID>`，round+1，`--resume` 继续
- round ≥ maxRounds 时强制 escalate，删 `.review-session-<SESSION_ID>`
