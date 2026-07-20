---
name: audit-salary
description: 薪酬审计——全量扫描重复计薪/缺失/daily不一致，逐日定位根因，指引修复与验证。触发：/audit-salary、审计薪酬、查薪酬、薪酬重复、daily不一致、检查薪酬。
allowed-tools: Read, Write, Bash
---

# /audit-salary — 薪酬审计

全量 8 维度审计 → 逐日定位根因 → 修复 → 验证。

## 硬约束

1. 审计阶段纯只读，不写库
2. 修复前强制确认 + 备份表
3. 试点优先于全量（10 条 → 一个工厂一天 → 全量）
4. 修复后必须重跑审计确认 PASS

## 流程

### 步骤 1：参数确认

收集 uid + 月份。uid 未知时查 [[fa56-store-factory-uid-map]]。

### 步骤 2：全量审计（只读）

1. 复制 `fa56-php/proc/tests/audit_june_salary.php` 为临时脚本
2. 修改 `$filter_uid` + SQL 中所有日期字符串
3. 运行：
   ```bash
   docker exec fa56-php-php-fpm-1 php /var/www/html/proc/tests/<临时脚本>.php
   ```
4. 解析 8 维度输出，重点关注 `[FAIL]` 和 `[WARN]`：
   - 维度 1（正向缺失）→ 工序未生成薪酬
   - 维度 6（daily 交叉校验）→ daily 与 salary_log 不一致
   - 维度 8（重复检测）→ (lid,wid) 重复
   - 维度 7（worker 余额 WARN）→ 通常是假阳性，忽略

全部 PASS → 结束，清理临时脚本。

### 步骤 3：逐日定位（仅 FAIL 时）

修改 `fa56-php/proc/tests/_diag_daily_detail.php` 的 `$uid` + SQL 日期 → 运行，定位偏差日期和工人。

### 步骤 4：修复 + 验证

**daily 不一致**：修改 `_rebuild_daily_2294.php` 的 `$uid`/`$date_start`/`$date_end` → 全月重建（不要逐日挑修）。

**重复记录**：试点展示 → 物化 ID 表 → 分批 1000 条/批 + 0.2s sleep → 验证。

修复后重跑步骤 2，确认 PASS。

## 关键参考

- [[salary-audit-fix-lessons]] — 9 节完整经验 + 常见坑速查
- [[daily-pairs-rebuild-after-fix]] — 修复后必须重建 tmp_affected_daily_pairs
- [[salary-log-created-at-align-finish-time]] — 补插记录 created_at 对齐 finish_time
- `fa56-php/docs/salary-calculation-logic.md` — 薪酬计算全链路文档

## 常见坑

| 症状 | 根因 | 解决 |
|------|------|------|
| 审计 1 缺失率高 | 包含"未排产"等不计薪工序 | 假阳性，维度 3 单独列出 |
| daily < salary_log | 重建漏了五金（amount=0） | 确保聚合不过滤 `amount>0` |
| 诊断显示偏差但实际一致 | 诊断脚本与重建脚本聚合口径不同 | 统一口径 |
| worker 余额大量 WARN | income2 是终身累计 | 忽略，除非 >200% |
| 重复清理后残留 | 分批删时子查询漂移 | 必须先物化 ID 表 |
