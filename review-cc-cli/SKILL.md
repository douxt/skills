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

| 用法 | 分类 | 说明 |
|------|------|------|
| `/review` | — | 默认审查未提交改动 |
| `/review <文件\|目录\|git范围>` | 范围 | 指定审查对象 |
| `/review --opus` | 模型 | 最强模型（**默认**） |
| `/review --sonnet` | 模型 | 平衡模型 |
| `/review --haiku` | 模型 | 快速评审，最省 |
| `/review --model <ID>` | 模型 | 自定义任意模型 |
| `/review --shallow` | 上下文 | 只看 diff，不读额外文件 |
| `/review --explore` | 上下文 | 允许 grep/读相关文件深入了解 |
| `/review --rubric <名称>` | 标准 | 指定评审标准文件 |

### 模型映射

子进程 `claude -p` 默认使用系统的当前模型。先读 `~/.claude/settings.json` 获取自定义模型 ID，没有再回退：

| 参数 | 读取配置键 | 回退 | 默认 |
|------|-----------|------|------|
| `--opus`（默认） | `ANTHROPIC_DEFAULT_OPUS_MODEL` | `ANTHROPIC_MODEL` → 不传 | **默认** |
| `--sonnet` | `ANTHROPIC_DEFAULT_SONNET_MODEL` | `ANTHROPIC_MODEL` → 不传 | |
| `--haiku` | `ANTHROPIC_DEFAULT_HAIKU_MODEL` | `ANTHROPIC_MODEL` → 不传 | |
| `--model <原始ID>` | 直接传递 | — | |

模型参数与上下文参数独立，可组合使用。默认 `--opus`。

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
| `--explore` | 可 grep 项目结构、读相关模块 | 跨模块改动、架构评审 |

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
  ③ 构造 claude -p 命令（只传 --model <ID>，不传 skill 自有参数）
  ③-1 安全自查：确认命令中不含 --opus/--sonnet/--haiku/--explore/--shallow 等 skill 自有开关
  ④ Bash: claude -p --model opus --permission-mode auto \
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
  ⑦ 读取 `.review-report-<slug>.json`，提取 criticalIssues 列表
  ⑧ 逐条核实子进程的发现：
     - Read 对应文件/行获取源码上下文
     - 判断是否为真实问题（排除 false positive）
     - 判断严重级别是否恰当
     - 标记可疑项 / 补充遗漏
  ⑨ 输出最终评估报告：
     - ✅ 已确认的问题（保持或调整 severity）
     - ⚠️ 存疑/误报（附排除理由）
     - 🔍 追加发现（如有）
     - 📊 评审质量总结
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

主实例从 `result` 字段的文本中提取上述 JSON 块。

### 最终评估报告格式

主实例在步骤 ⑨ 汇总以下内容：

```
🔍 最终评估报告

✅ 已确认的问题：
  1. [high] path/file.js:42 — 问题描述（子进程原判）
     → 核实结论：真实问题，严重级别合适

⚠️ 存疑/误报：
  1. path/file.js:88 — 原判 XX 问题
     → 排除理由：此处已在前置条件中处理，不会到达

🔍 追加发现（主进程补充）：
  1. [medium] path/other.js:15 — 遗漏的 XX 问题

📊 评审质量总结：
  - 总发现数：N
  - 确认数：N
  - 误报数：N
  - 补充数：N
  - 评审质量评价：良好/一般/需改进
```

## 最佳实践推荐

输出最终评估报告时，若涉及计划/实施类评审任务，向用户推荐以下实践：

### 逐步骤验证门禁

计划中的每个步骤都应有独立的验证手段：

```
步骤 N 实施完毕
  ↓
① 验证此步骤改动符合计划预期
② 确认未破坏前面已完成步骤
③ 通过 → 继续；阻塞 → 修正
```

Rubric 的 plan.md 已包含此项检查。

### 三个关键门禁

| 门禁 | 时机 | 检查什么 |
|------|------|---------|
| Plan Review | 执行前 | 方案合理性 + 每步有验证手段 |
| Findings Review | 探索后、改代码前 | 实际代码情况是否改变了原计划 |
| Diff Review | 改完后、提交前 | 实际改动是否符合预期 |

### 核心原则

> 每一步必须有可证伪的验证（不是"看起来 OK"），通过才能继续下一步。

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
