---
name: review-cc-cli
description: Use when needing an independent code review of current changes before committing or merging
allowedTools: Read,Grep,Glob,Bash
license: MIT
---

# /review-cc-cli

## 安装

```
# 1. 将 skill 放到 ~/.claude/skills/
cp -r review-cc-cli ~/.claude/skills/review-cc-cli

# 2. 部署配置 + rubrics
cd ~/.claude/skills/review-cc-cli && bash scripts/install.sh
```

之后在任意项目中执行 `/review-cc-cli` 即可。

在当前对话中启动一个**独立上下文**的 `claude -p` 实例，只读评审代码/计划/测试。
多轮评审**复用同一 session**，第 2 轮起利用 prompt cache 大幅降本。

## 评审范围指定

`/review-cc-cli` 支持灵活指定评审内容：

| 用法 | 分类 | 说明 |
|------|------|------|
| `/review-cc-cli` | — | 默认审查未提交改动 |
| `/review-cc-cli <文件\|目录\|git范围>` | 范围 | 指定审查对象 |
| `/review-cc-cli --opus` | 模型 | 最强模型（**默认**） |
| `/review-cc-cli --sonnet` | 模型 | 平衡模型 |
| `/review-cc-cli --haiku` | 模型 | 快速评审，最省 |
| `/review-cc-cli --model <ID>` | 模型 | 自定义任意模型 |
| `/review-cc-cli --shallow` | 上下文 | 只看 diff，不读额外文件 |
| `/review-cc-cli --explore` | 上下文 | 允许 grep/读相关文件深入了解 |
| `/review-cc-cli --rubric <名称>` | 标准 | 指定评审标准文件 |
| `/review-cc-cli --quick` | 模式 | 跳过主进程自评估（⑧-⑨），直接输出子进程结果，省 token |
| `/review-cc-cli --loop` | 模式 | 自动收敛循环：多轮独立评审，3 轮无新发现自动停止 |
| `/review-cc-cli --loop-rounds <N>` | 模式 | 最大轮次上限（默认 10），与 `--loop` 配合使用 |
| `/review-cc-cli --loop-budget <tokens>` | 模式 | token 预算上限，与 `--loop` 配合使用。不传则不限制 |
| `/review-cc-cli --help` | — | 显示完整使用说明（不启动子进程） |

> `--loop` 与 `--quick` 互斥，同时指定时报错。

### 模型映射

skill 不读 `settings.json`（避免触碰敏感配置），模型别名直接透传给 `claude -p`，由 CLI 自身通过环境变量解析：

| 参数 | 传给 claude -p | 说明 |
|------|---------------|------|
| `--opus`（默认） | `--model opus` | CLI 查 `ANTHROPIC_DEFAULT_OPUS_MODEL` 环境变量解析 |
| `--sonnet` | `--model sonnet` | CLI 查 `ANTHROPIC_DEFAULT_SONNET_MODEL` 环境变量解析 |
| `--haiku` | `--model haiku` | CLI 查 `ANTHROPIC_DEFAULT_HAIKU_MODEL` 环境变量解析 |
| `--model <ID>` | `--model <ID>` | 直接透传 |

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
你 → /review-cc-cli [范围]
      ↓
主实例（当前对话）:
  ① 确定评审范围
  ② git diff --stat 确认变更集
  ③ 构造 claude -p 命令：将 skill 参数映射为 --model <别名>（如 --opus → --model opus），不传其他 skill 自有参数
  ③-1 安全自查：确认命令中不含 --explore/--shallow/--quick/--loop 等非模型类 skill 自有开关
  ④ Bash: claude -p --model <模型ID> --permission-mode auto \
          --settings ~/.claude/settings-review.json --output-format json
          （首次创建新 session；后续 --resume <session_id> 重用）
      ↓
步骤 ④ 构造子进程 prompt：
  要求子进程：
    - Read 要评审的文件
    - Read ~/.claude/review-rubrics/{rubric}.md 获取评审标准
    - 输出 JSON 格式结果（在回复中包含以下定义的 JSON 结构）
      ↓
子实例执行评审。`claude -p --output-format json` 返回外层结构
`{type, result, session_id, ...}`，result 字段为子进程完整回复。
      ↓
主实例:
  ⑤ 从外层 JSON 提取 session_id（会话管理用）和 result 文本
  ⑥ 写会话文件：
      文件名：.review-session-${CLAUDE_CODE_SESSION_ID}
      内容：{"sessionId":"<子进程 session_id>","round":<N>,"maxRounds":3}
     （若 round ≥ maxRounds，删除会话文件）
  ⑦ 从 result 文本中提取子进程输出的 JSON 评审结果
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

> 指定 `--quick` 时跳过 ⑧-⑨，步骤⑦之后直接展示子进程原始结果。
```

## Loop 模式 (`--loop`)

自动收敛循环：多次独立评审直到不再发现新问题。

### 关键取舍

| 取舍点 | loop 模式的选择 | 原因 |
|--------|---------------|------|
| session 复用 | **每轮新建**，不用 `--resume` | 子进程必须独立，否则后续评审丧失独立性 |
| 用户交互 | **全自动** | 需人工介入走手动 `/review-cc-cli`，loop 定位是全自动收敛 |
| 成本 | 接受每轮全价 | independence > cache savings |
| 确认即修 | **自动修改文件** | 每轮评估确认后立即 Edit 源文件，下一轮子进程审阅最新版本 |
| 修改边界 | **强制写入，不可拖延** | 确认即 Edit 文件；唯一例外是架构变更需人工，但也须写 TODO 注释 |

### 状态文件

`.review-loop-state-${CLAUDE_CODE_SESSION_ID}`（`CLAUDE_CODE_SESSION_ID` 未设时用 `.review-loop-state`），与 `.review-session-<SESSION_ID>` 并存，互不干扰：

```json
{
  "totalRounds": 0,
  "maxRounds": 10,
  "totalTokensUsed": 0,
  "budgetLimit": null,
  "acceptedIssues": [],
  "rejectedIssues": [],
  "roundHistory": [],
  "errors": [],
  "consecutiveEmptyRounds": 0,
  "lastError": null,
  "done": false
}
```

`roundHistory` 每条记录：
```json
{"round": 1, "found": 5, "confirmed": 2, "rejected": 3, "tokens": 12000}
```

`errors` 每条记录：
```json
{"round": 2, "type": "security_blocked|timeout|no_json|non_zero_exit", "detail": "..."}
```

### 循环流程

```
/review-cc-cli --loop <范围>
      ↓
主进程:
  ① 读取 .review-loop-state-${CLAUDE_CODE_SESSION_ID}
  ② 如果 done → 展示最终汇总，退出
  ③ 构造子进程 prompt：
     - 已确认并修正的问题（N 条）：列原始问题+修改内容，可验证修改是否正确
       - 若修正无误 → 无需再提
       - 若修正引入新问题或改错 → 按新 issue 报告
     - 已驳回的问题及理由（N 条）：已被判定无效，避免同类误报
     - 要求：独立评审，关注未覆盖问题，不预设「已过审就安全」
  ④ Bash: claude -p --model <模型ID> ... --output-format json
  ⑤ 提取子进程的 criticalIssues 列表
  ⑥ 子进程异常处理：
     超时/无有效 JSON:
       - 本轮不计，重试一次
       - 连续 2 次失败 → done=true，记录到 errors，输出中断提示
     被安全拦截（权限拒绝/安全 hook 阻止/非零退出码无输出）:
       - 本轮不计，不重试（重试必然再被拦）
       - 立即记录到 errors，在汇报中明确告知用户拦截原因
       - 不影响已有结果，继续下一轮
       - 若全部轮次被拦截（totalRounds=0 且 errors 非空）→ 输出失败汇总
  ⑦ 逐条评估（全自动，用户不介入）：
     - Read 源码 → 合理 → 加入 acceptedIssues（file:line 去重）
     - Read 源码 → 不合理 → 加入 rejectedIssues + 理由
     - 模糊问题标注置信度（高/中/低）
  ⑧ 应用修正（强制，不可跳过）：
     - 对新确认的每条 issue，必须立即 Edit 写入源文件
     - 严禁以「实施时顺手改」「后续统一处理」等理由跳过写入
     - 唯一例外：涉及架构/逻辑变更超出纯文档范围 → 标注需人工确认，并写入 TODO 注释到文件中
     - 修改后确认文件已保存，下一轮子进程审阅的是最新版本
  ⑨ 本轮无新确认 → consecutiveEmptyRounds++
     否则 → consecutiveEmptyRounds = 0
  ⑩ 从 claude -p 输出中提取 usage tokens，累加到 totalTokensUsed
      追加 roundHistory 记录：{round, found, confirmed, rejected, tokens}
  ⑪ 写入 .review-loop-state-${CLAUDE_CODE_SESSION_ID}
  ⑫ 停止条件（优先级从高到低）：
     A. budgetLimit 已设 且 totalTokensUsed ≥ budgetLimit → 达预算
     B. consecutiveEmptyRounds ≥ 3 → 已收敛
     C. totalRounds ≥ maxRounds → 达上限
  ⑬ 满足任一 → done=true，写状态文件，输出最终汇总，退出
  ⑭ 输出本轮汇报：
     📋 第 N 轮完成
     🔍 本轮子进程发现 X 条，主进程确认 Y 条，驳回 Z 条
     🚫 本轮异常（如有）：
       - 安全拦截：<原因>（权限拒绝/退出码 N）
     ✅ 本轮新确认（已修改）：
       1. [high] file:line — 描述 ✓ 已应用
     ⚠️ 确认但跳过（需人工判断）：
       1. [medium] file:line — 描述 → 跳过原因
     ⛔ 本轮驳回：
       1. file:line — 描述 → 驳回理由
     📊 累计：N 轮，确认 N 条（已修 N 条），驳回 N 条，异常轮次 N，空轮 N，token N
     ➡️ 继续下一轮（子进程将审阅修改后的文件）...
  ⑮ 立即回到③（全自动，不询问不等待，禁止在此处打断循环）
```

### 最终汇总

```
🔍 自动评审循环结束（原因：收敛/达上限/达预算/异常中断）

📊 逐轮明细：
  轮次  发现  确认  驳回  异常       token
  ────────────────────────────────────────
  1     5     2     3     —          12000
  2     3     1     2     安全拦截    8000
  3     4     1     3     —          9500
  ...

✅ 已确认并采纳的问题（共 N 条）：
  1. [high] src/a.js:42 — 描述（第1轮确认）

⛔ 已驳回的问题及理由（共 N 条）：
  1. src/b.js:88 — 描述 → 驳回理由（第1轮驳回）

🚫 异常记录（如有）：
  第2轮：安全拦截 — 权限拒绝，xxx 文件不可读

📊 共 N 轮评审，确认 N 条，驳回 N 条，异常 N 次，总 token N
```

## 子进程输出格式

主实例解析子进程的 JSON 输出时，子进程 prompt 必须要求以下 JSON 结构：

```json
{
  "verdict": "APPROVED | CHANGES_REQUESTED | BLOCKED",
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

| 门禁 | 时机 | 检查什么 | 对应 skill 用法 |
|------|------|---------|----------------|
| Plan Review | 执行前 | 方案合理性 + 每步有验证手段 | `--rubric plan <plan.md>` |
| Findings Review | 探索后、改代码前 | 实际代码情况是否改变了原计划 | `--explore <目录>` |
| Diff Review | 改完后、提交前 | 实际改动是否符合预期 | `/review-cc-cli <文件>`（默认模式） |

### 核心原则

> 每一步必须有可证伪的验证（不是"看起来 OK"），通过才能继续下一步。

## --help 输出

触发 `/review-cc-cli --help` 时输出：
1. 所有参数列表及说明（用法表）
2. 用法示例 3-5 条
3. Rubric 自动匹配规则表
4. Loop 模式说明和流程图
5. 错误处理概览

## 错误处理

子进程 `claude -p` 可能失败，定义以下降级策略：

| 场景 | 处理 |
|------|------|
| `claude` 命令不存在 | 告知用户，降级为当前对话内直接评审 |
| 子进程超时（>60s） | 重试一次，再失败则提示用户手动检查 |
| 输出无有效 JSON 块 | 把原始文本当评审报告展示 |
| 子进程被安全拦截（权限拒绝/非零退出码） | 不重试，记录到 errors，汇报中明确告知原因，继续下一轮 |
| diff 为空（git diff 无输出） | 提示无改动，跳过子进程 |
| `CLAUDE_CODE_SESSION_ID` 未设 | 步骤⑥用固定名 `.review-session` 代替 |
| rubric 文件缺失 | 降级为 default rubric，记录日志 |
| `--resume` 到已过期/不存在的 session | 重新创建新 session，提示用户 |
| 全部轮次被拦截（totalRounds=0 且 errors 非空） | 输出失败汇总，列出每次拦截原因 |

## 多轮会话复用

- `.review-session-<SESSION_ID>` 存储 `{"sessionId": "abc123", "round": 1, "maxRounds": 3}`
  - `<SESSION_ID>` 从环境变量 `CLAUDE_CODE_SESSION_ID` 获取，每个会话独立
  - 主实例在步骤 ⑤-⑥ 负责读写此文件
  - 并发会话各自读写自己的文件，不冲突
- 首次 `/review-cc-cli` → round=1，创建 session，写 `.review-session-<SESSION_ID>`
- 后续 `/review-cc-cli` → 读 `.review-session-<SESSION_ID>`，round+1，`--resume` 继续
- round ≥ maxRounds 时强制 escalate，删 `.review-session-<SESSION_ID>`
