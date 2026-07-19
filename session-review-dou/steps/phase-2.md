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

诊断完成后展示总览，用户确认后进入阶段 3。

（阶段 2 结束。完成后加载 steps/phase-3.md）
