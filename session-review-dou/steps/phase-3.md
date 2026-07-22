# 阶段 3：建议生成

## 决策树

对每个发现：
```
→ ≥3 个不同会话 AND 跨 ≥2 天？
  ├─ 否 → 记录到临时关注列表（告知用户但不写文件）
  └─ 是 → 去重（对照阶段 2 中已读的 CLAUDE.md + memory/）
           ├─ 已覆盖 → 只更新已有规则的 xN 计数器
           ├─ 新发现 → 定目标：
           │   ├─ 本项目行为规范 → CLAUDE.md
           │   ├─ 跨项目通用踩坑 → memory/
           │   ├─ 可封装重复流程 → 确认后启动 skill-creator
           │   └─ 一次性小修正 → 直接修复代码
           └─ 无合适目标 → 解释原因
```

## 写入规则

在 CLAUDE.md 中写入时：
- **不追加到文件末尾**。先读目标文件已有章节结构，按话题插入对应节下。
- 若目标文件无对应节，新建 `## Lessons` 节（在非 lessons 内容之后）。
- 格式：`- [x1] Mistake: <描述> | Correct: <正确做法> | Why: <原理>`

在 memory/ 中写入时：
- 单文件一个事实。frontmatter 含 name/description/tags。
- 格式参考项目已有 memory/ 文件。

## 输出建议列表

每条建议附带具体命令/代码模板，用户可直接复制执行：

```
## 建议行动

### P0 — 立即执行（已导致实质性返工）
1. [CLAUDE.md] 开工前基线核查
   规则：方案中任何数量型事实，开工前亲自执行命令确认
   来源：会话 A msg 45、会话 B msg 120

### 💡 最佳实践升级（可直接执行）
2. [/schedule] 流水线健康检查自动化
   当前：每次手动 pgrep+curl+awk（会话 #3 中 ~25 次）
   建议：`/schedule every 1h: pgrep -x python3 && curl -s :4416/ping`
   参考：analysis/cross-cutting/goal-command-guide.md

3. [/goal] 视频总结质量验证
   当前：每次手动看 frontmatter 是否完整
   建议：`/goal 检查 /data/docs/ 最近 3 天总结的 frontmatter 完整性 until 全部含 video_id+title+date stop after 3 turns`

### 已固化（本次发现已有规则覆盖）
4. ✅ 意图对齐 — 已写 lessons（AI 默认假设纠正）
```

（阶段 3 结束。完成后加载 steps/phase-4.md）
