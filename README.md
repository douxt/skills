# skills

Claude Code 技能集合。

## 技能列表

| 技能 | 说明 |
|------|------|
| [review-cc-cli](review-cc-cli/) | 通过 `claude -p` 子进程进行独立代码审查 |

## 安装技能

```bash
# npx skills 方式（自动安装到 ~/.claude/skills/）
npx skills add douxt/skills -g -a claude-code -y

# 手动方式
git clone https://github.com/douxt/skills.git
cp -r skills/<skill-name> ~/.claude/skills/<skill-name>
cd ~/.claude/skills/<skill-name> && bash scripts/install.sh
```

## 贡献

欢迎提交 PR 或新 skill。目录结构：

```
skills/
├── README.md
├── <skill-name>/
│   ├── SKILL.md          # 技能指令（Claude 加载的核心）
│   ├── README.md         # 技能说明（GitHub 展示）
│   ├── LICENSE
│   ├── scripts/          # 安装/辅助脚本
│   ├── config/           # 配置文件
│   └── rubrics/          # 审查标准等资源文件
└── ...
```

---

# skills

A collection of Claude Code skills.

## Available Skills

| Skill | Description |
|-------|-------------|
| [review-cc-cli](review-cc-cli/) | Independent code review via `claude -p` sub-process |

## Installation

```bash
# Via npx skills (auto-installs to ~/.claude/skills/)
npx skills add douxt/skills -g -a claude-code -y

# Manual
git clone https://github.com/douxt/skills.git
cp -r skills/<skill-name> ~/.claude/skills/<skill-name>
cd ~/.claude/skills/<skill-name> && bash scripts/install.sh
```

## Contributing

PRs welcome. Structure:

```
skills/
├── README.md
├── <skill-name>/
│   ├── SKILL.md          # Skill instructions (loaded by Claude)
│   ├── README.md         # Human-readable docs (shown on GitHub)
│   ├── LICENSE
│   ├── scripts/          # Install/utility scripts
│   ├── config/           # Configuration files
│   └── rubrics/          # Review criteria, resources
└── ...
```
