# 开发流程固化：最佳实践与推荐方案

## 问题

AI 辅助开发中，流程靠人记、靠自觉调用，导致：
- 忽评忽不评，取决于当时想不想得起来
- 步骤顺序飘移（有时先写代码后补计划，有时反过来）
- 新人/新项目没有流程可循，从零摸索

目标：将「计划→PRD 评审→编码→代码评审→提交」固化为可复用、可发布、可跳过的工程流程。

## 方案对比

| 方案 | 固化程度 | 复杂度 | 可分发 | 灵活性 |
|------|---------|--------|--------|--------|
| A: Skills + Rubrics + CLAUDE.md 约定 | 低（靠自觉） | 最低 | ✅ 单 repo | 最高 |
| B: Skills + settings.json Hooks | 中（关键节点强制） | 低 | ✅ 单配置 | 高 |
| C: Archon YAML 工作流 | 高（DAG 强制执行） | 高（Docker + MCP） | ✅ 随仓库 | 中 |
| D: B + C 混合 | 高（核心钩子 + 复杂场景工作流） | 中-高 | ✅ | 高 |

## 推荐：方案 D（渐进式固化）

### 第一层：基础约束（settings.json hooks）

在 `~/.claude/settings.json` 中配置 hook，在关键节点自动触发 review：

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "command": "git commit",
        "hooks": [{
          "type": "command",
          "command": "claude -p \"运行 /review-cc-cli 检查当前改动...\" "
        }]
      }
    ]
  }
}
```

此层作用：git commit 前自动触发代码评审，不靠人记。

### 第二层：结构化流程（skills 串联）

将现有 skills 串成标准开发流水线：

```
/plan-prd <需求>           → 产出 PRD（to-prd skill）
    ↓
/review-cc-cli --rubric prd  → PRD 评审（prd.md rubric）
    ↓
/plan <PRD>                → 产出实现计划
    ↓
/review-cc-cli --rubric plan → 计划评审（plan.md rubric + worktree 检查）
    ↓
编码实现                     → 在 worktree 中开发
    ↓
/review-cc-cli [--loop]    → 代码评审（可循环收敛）
    ↓
git commit && git push     → 提交（hook 自动触发最终检查）
```

每个 `/review-cc-cli` 步骤可被用户跳过（`--quick`），灵活度保留。

### 第三层：复杂场景（Archon 工作流）

当项目规模大、多人协作、需要严格门禁时，将上述流程写成 Archon YAML 工作流：

```yaml
nodes:
  - id: prd
    prompt: "基于需求生成 PRD"
  - id: review-prd
    depends_on: [prd]
    prompt: "/review-cc-cli --rubric prd <prd文件>"
  - id: plan
    depends_on: [review-prd]
    prompt: "基于 PRD 创建实现计划（含 worktree 创建步骤）"
  - id: review-plan
    depends_on: [plan]
    prompt: "/review-cc-cli --rubric plan <plan文件>"
  - id: implement
    depends_on: [review-plan]
    loop:
      prompt: "读取计划，实现下一个任务"
      until: ALL_TASKS_COMPLETE
  - id: review-code
    depends_on: [implement]
    prompt: "/review-cc-cli --loop <改动范围>"
  - id: approve
    depends_on: [review-code]
    interactive: true
```

## 实施路径

1. **立即可做**：把 prd.md rubric + plan.md rubric + review-cc-cli SKILL.md 作为一套发布
2. **短期**：写一个安装脚本，一键部署 skills + rubrics + hooks 配置
3. **中期**：加 Archon 工作流 YAML 到 skills 仓库，用户可选启用
4. **长期**：做成 `npx skills add douxt/dev-workflow` 一键安装全套

## 核心原则

- **固化不僵化**：每一步都可跳过或简化（`--quick`/`--scope`/直接跳过）
- **渐进接入**：新人可以从单个 skill 用起，不用一次全装
- **工具无关**：流程描述不绑定具体工具名（worktree 不写成 `wt create`）
- **评审必带参考文档**：代码评审必须 `--with` 需求/设计文档
