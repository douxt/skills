# 阶段 2：会话尸检 — 诊断分析

## 准备

1. 读 `rubrics/dimensions.md` 获取六维诊断框架 + root cause 五分类 + lessons 格式
2. 读 CLAUDE.md + memory/MEMORY.md → 标记已有覆盖的规则（去重用）
3. 读 `reviews/` 下最近一次归档 → 对比上次发现：
   - 若同类信号本次消失或减少 → 标记 ✅ 规则生效
   - 若同类信号仍在犯 → 标记 ⚠️ 规则未生效，需要检查规则措辞/位置

## 诊断

对每个选中会话的摘要，逐维度诊断。每个发现必须附带：
- **原文 verbatim 引用**：从 user_sample 或 assistant_sample 中提取精确原句
- **root cause 分类**：从五分类中选一个
- **评分标记**：✅ 无问题 / ⚠️ 轻微 / ❌ 严重 / 💡 升级机会

输出格式：
```
## 会话 <id> — <日期>

| 维度 | 评分 | Root Cause | 证据 |
|------|------|-----------|------|
| 意图对齐 | ⚠️ | missing context | > "不是那个字段" (user msg) |
| 完成验证 | ❌ | ignored instructions | AI: "完成了" → 用户: "你确认过？" |
| 错误固化 | ✅ | — | — |
| 循环升级 | 💡 | missing instructions | 手动触发 ×3 次，可升 /goal |
| 范围纪律 | ⚠️ | wrong approach | 方案 24 篇 → DB 实际 33 篇 |
| 上下文韧性 | ❌ | tool misuse | 子代理集体幻觉 |
```

## 最佳实践对照

读完诊断结果后，对照最佳实践知识库，为每个 💡/⚠️ 发现生成具体升级建议：

| 检测模式 | 推荐实践 | 具体命令模板 |
|---------|---------|------------|
| 同一命令重复 ≥5 次 | 升级为 /goal | `/goal [任务] until [可量化的完成条件] stop after N` |
| 定时手动检查 ≥3 次 | 升级为 /schedule | `/schedule every 1h: [命令]` |
| 多步骤手动流程 ≥2 次 | 封装为 skill | 创建 SKILL.md，参考 session-review-dou 模板 |
| 同一错误重复 ≥2 次 | 写入 lessons | `- [xN] Mistake: ... Correct: ... Why: ...` |
| AI 猜错你的意图 | 加反向复述检查点 | "动代码前先用自己话写对关键字段的理解" |
| 多会话重复任务 | 升级为 Routine | 管道 source + db pending 队列 |

参考文档：`analysis/cross-cutting/goal-command-guide.md`（/goal 完整指南）、`rules/session-lessons.md`（跨项目教训）

诊断完成后展示总览，用户确认后进入阶段 3。

（阶段 2 结束。完成后加载 steps/phase-3.md）
