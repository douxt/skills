# session-review-dou

会话尸检（Session Autopsy）。扫描 Claude Code 历史会话，六维诊断错误模式，给出从 Turn-based 向 Proactive 升级的行动路径。

## 六维诊断框架

| 维度 | 检测 | 输出 |
|------|------|------|
| 意图对齐 | AI 猜错了你的意思？ | 反向复述检查点 |
| 完成验证 | AI 声称完成但真做完了？ | 机器可检查完成标准 |
| 错误固化 | 纠正了，下次还犯吗？ | lessons 规则写入 |
| 循环升级 | 重复任务还是手动触发？ | 建议升级 /goal |
| 范围纪律 | 方案过度工程？基线核实过？ | 开工前核查 |
| 上下文韧性 | 长会话丢决策？子代理编造？ | 双重验证 + ADR |

## 安装

### npx skills（推荐）

```bash
npx skills add douxt/skills -g -a claude-code -y
```

### 手动

```bash
git clone https://github.com/douxt/skills.git
cp -r skills/session-review-dou ~/.claude/skills/session-review-dou
```

## 使用

```bash
/session-review-dou          # 列出会话，选最多 3 个分析
/session-review-dou 1 3      # 直接选编号 1 和 3
/session-review-dou all      # 扫所有会话（≥30 天）
```

## Stop Hook（可选）

在 `~/.claude/settings.json` 中配置，会话结束时自动提醒：

```json
{
  "hooks": {
    "Stop": [{
      "matcher": "",
      "command": "python3 ~/.claude/skills/session-review-dou/scripts/check_session_size.py"
    }]
  }
}
```

## 结构

```
session-review-dou/
├── SKILL.md           # 核心指令（阶段 1）
├── README.md
├── steps/              # 阶段 2-4 按需加载
├── scripts/
│   ├── scan.py         # 会话扫描 + jq/Python 双模
│   └── check_session_size.py
├── rubrics/
│   └── dimensions.md   # 六维框架 + root cause + lessons 格式
├── config/
│   └── signals.json    # 中英文信号初筛
└── reviews/            # 分析归档（git 同步）
```

## 与其他工具对比

| | craftwork/retro | meain/retrospect | session-review-dou |
|---|---|---|---|
| 诊断深度 | 一维（有无错误） | 手动判断 | 六维 + root cause 五分类 |
| 闭环验证 | 无 | 无 | 下次对比同类信号 |
| 中文支持 | 无 | 无 | 中英文双模 |
| 跨机器 | 不支持 | 不支持 | reviews/ 随 git 同步 |
| 升级路径 | 无 | 无 | Turn-based→Proactive 阶段建议 |
