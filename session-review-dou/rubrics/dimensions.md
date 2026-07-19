# 六维诊断 + Root Cause 分类

## 六维

### 1. 意图对齐
检测 AI 猜错字段/路径/含义、方案方向错误、用户纠正说"不是""不对"。
信号：理解振荡（两错误间来回跳）、前提歧义。
关联 root cause：missing context / wrong approach。
建议：反向复述检查点、开工前前提确认。

### 2. 完成验证
检测 AI 声称完成但无运行日志/截图/测试结果。
信号：用户质疑"真的吗？"、之后发现未完成。
关联 root cause：ignored instructions / tool misuse。
建议：机器可检查完成标准、独立 evaluator、显式 Receipt。

### 3. 错误固化
检测同一错误重复 ≥2 次、纠正后未写入规则。
信号：CLAUDE.md 无 #Lessons 节、Boris 自学习片段未启用。
关联 root cause：missing instructions。
建议：纠正 → 写规则 → xN 计数器。

### 4. 循环升级
检测重复任务仍手动触发、可量化标准已具备但未用 /goal。
信号：手动触发 ≥3 次、完成标准可机器检查。
关联 root cause：missing instructions（不知道可用 /goal）。
建议：升级到 Goal-based / Time-based。

### 5. 范围纪律
检测方案复杂度不匹配实际规模、开工前未核实基线。
信号：方案写 N 实际 M（偏差 >20%）。
关联 root cause：wrong approach。
建议：开工前基线核查、约束参数前置、标注必要/可选。

### 6. 上下文韧性
检测 /compact 丢决策、子代理编造事实、长会话质量崩塌。
信号：子代理集体幻觉、压缩后遗忘关键决策。
关联 root cause：missing context / tool misuse。
建议：决策 ADR、子代理前提验证、双重验证。

## Root Cause 五分类

1. **missing instructions** — 没告诉 AI 怎么做 → 加规则
2. **ignored instructions** — 告诉了没执行 → 措辞更明确、加硬性检查
3. **wrong approach** — AI 选次优策略 → 加约束、给范例
4. **missing context** — AI 缺关键信息 → 补充领域知识
5. **tool misuse** — AI 用错工具 → 限定 allowed-tools

## Lessons 格式

```
- [xN] Mistake: <错误>
  Correct: <正确做法>
  Why: <原理>
```
上限 15 条。xN 低者或最旧者优先淘汰。x3 后提升为永久规则。
