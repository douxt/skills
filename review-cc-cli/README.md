# review-cc-cli

在当前对话中启动一个**独立上下文**的 `claude -p` 实例，只读评审代码/计划/测试。多轮评审复用同一 session 以降本。

## 核心特性

- **独立子进程审查** — 子进程有独立的上下文，不受当前对话影响
- **多轮会话复用** — 第 2 轮起利用 prompt cache 大幅降本
- **Rubric 驱动** — 按路径自动匹配审查标准（security/performance/plan 等）
- **模型选择** — `--opus`(默认) `--sonnet` `--haiku` 或 `--model <ID>` 指定任意模型
- **范围灵活** — 当前 diff、指定文件、目录、git 范围均可

## 安装

### 方式一：npx skills（推荐）

```bash
npx skills add douxt/skills -g -a claude-code -y
./scripts/install.sh     # 部署配置文件 + rubrics
```

### 方式二：手动

```bash
git clone https://github.com/douxt/skills.git
cp -r skills/review-cc-cli ~/.claude/skills/review-cc-cli
cd ~/.claude/skills/review-cc-cli && bash scripts/install.sh
```

## 使用

```bash
/review              # 审查未提交改动
/review src/         # 审查指定目录
/review --rubric security src/auth/   # 用安全标准审查
/review --explore src/                # 探索式审查（深入读相关文件）
/review HEAD~3       # 审查最近 3 个 commit
```

## 结构

```
review-cc-cli/
├── SKILL.md               # 技能指令
├── scripts/
│   └── install.sh         # 部署配置 + rubrics
├── config/
│   └── settings-review.json  # 子进程权限配置
└── rubrics/               # 审查标准
    ├── default.md
    ├── security.md
    ├── performance.md
    ├── plan.md
    ├── config.md
    └── testing.md
```

## License

MIT

## 规划

### 下一步

- **`--fix` 模式** — 子进程审完同时对简单问题（格式/lint/风格）直接出 diff
- **Review 预算控制** — `--budget <tokens>`，按 token 预算智能分配审查深度
- **交互式 drill-down** — 自评估后可继续追问「这条展开看看」「这个 false positive 为什么」

### 远期展望

| 方向 | 思路 |
|------|------|
| 多视角并行评审 | 同时启动多个子进程（安全/性能/正确性各一路），合出综合报告 |
| 多语言专属 rubric | 根据文件后缀自动加载对应标准（`.py`→Python、`.php`→PHP 5.6 等） |
| 审查置信度标注 | 对每条发现给出 confidence（高/中/低），降低误报干扰 |
| 增量审查 | 大 PR 按文件分批审，避免超长 context 稀释质量 |
| 批量项目扫描 | 一次 review 跑遍多个关联仓库（前后端同时审） |
| pre-commit hook | 提交前自动 `--shallow` 拦截低级问题 |
| 自定义输出级别 | `--brief` 只给汇总，`--verbose` 给完整分析 |
| 架构模式检查 | 对比项目已有代码风格，发现不一致 |
| 团队 rubric 共享 | rubrics 独立仓，多 skill 共用 |
| 审查结果导出 | markdown/HTML 格式，方便贴到 PR 或文档 |
