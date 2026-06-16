# review-cc-cli

在当前对话中启动一个**独立上下文**的 `claude -p` 实例，只读评审代码/计划/测试。多轮评审复用同一 session 以降本。

## 核心特性

- **独立子进程审查** — 子进程有独立的上下文，不受当前对话影响
- **多轮会话复用** — 第 2 轮起利用 prompt cache 大幅降本
- **Rubric 驱动** — 按路径自动匹配审查标准（security/performance/plan 等）
- **模型选择** — `--fast` `--medium` `--deep` 或 `--model <ID>` 指定任意模型
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
/review --deep src/foo.js             # 深度审查（允许读相关文件）
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
