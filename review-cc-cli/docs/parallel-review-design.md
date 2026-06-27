# --parallel 并行评审设计文档

## 概述

在现有串行评审基础上，新增 `--parallel` 可选参数。启用后，多个独立 `claude -p` 子进程按维度并行评审，verifier 交叉检查去重合并，输出统一报告。

默认行为不变（串行），加 `--parallel` 才启用并行。

## 行业最佳实践吸收

### 1. 维度分离（Anthropic 内部 + CodeX-Verify）

每个 agent 只审一个维度，独立上下文避免锚定偏差：

| 维度 | Rubric | 阻断 | 关注点 |
|------|--------|------|--------|
| **correctness** | correctness.md | ✅ | 逻辑、边界、空值、类型、异常、状态、并发 |
| **security** | security.md | ✅ | OWASP top 10、注入、认证、密钥泄露 |
| **performance** | performance.md | ⚠️ | N+1、内存泄漏、阻塞 I/O、算法复杂度 |
| **style** | default.md | ❌ | 可维护性、命名、SOLID、DRY、死代码 |

> 审查顺序不可颠倒：correctness（阻断）→ security（阻断）→ performance（警告）→ style（建议）。

> 参考：Anthropic 内部 Explorer×N 模式——每个 explorer 独立搜索，互不知晓对方发现。

### 2. Verifier 交叉检查（`/ultrareview` 模式）

并行 explorer 输出 → 一个独立 verifier agent 逐条交叉验证：
- 去重：file:line 相同 → 合并，保留 severity 高者
- 诈骗检测：verifier Read 源码验证 explorer 的发现是否真实
- 降噪：verifier 确认后才进入最终报告

> 核心洞察：**找 bugs 和确认 bugs 是不同任务，不能绑在一个 agent 里。**

### 3. 对抗评分（PAR 模式）

两个 agent 同维度竞争 → 分歧时取 worst severity。
review-cc-cli 暂不采用（成本翻倍，收益有限），留作未来 `--adversarial` 扩展。

### 4. 自适应路由（ai-review-agent 模式）

分析 diff 内容后只激活相关维度：
- 纯 CSS 改动 → 不激活 security agent
- 纯测试文件 → 不激活 performance agent
- 认证模块 → 安全 agent 权重最高

review-cc-cli 第一版不实现自适应路由（增加复杂度），默认全维度激活，用户可 `--parallel security,correctness` 手动选择。

## 参数设计

```
/review-cc-cli --parallel [维度列表] [其他参数]
```

| 用法 | 说明 |
|------|------|
| `/review-cc-cli --parallel` | 4 维度全部并行（security/correctness/performance/style） |
| `/review-cc-cli --parallel security,correctness` | 仅安全和正确性两维 |
| `/review-cc-cli --parallel --loop` | 并行 + 循环收敛（每轮并行） |
| `/review-cc-cli --parallel --scope "第一批"` | 分批评审 + 并行 |

## 执行流程

```
/review-cc-cli --parallel <范围>
        │
  ① 主进程分析范围，确定激活维度
        │
  ② 并行启动 N 个 claude -p（Bash 后台任务）
     ┌────────┬────────┬────────┬────────┐
     │ claude │ claude │ claude │ claude │
     │  -p    │  -p    │  -p    │  -p    │
     │security│correct │  perf  │ style  │
     │rubric  │rubric  │rubric  │rubric  │
     └───┬────┴───┬────┴───┬────┴───┬────┘
         │        │        │        │
  ③ 收集所有 agent 的 JSON 输出
         │
  ④ 主进程初步去重（file:line 碰撞 → severity 取高）
         │
  ⑤ 启动 verifier agent（claude -p）
     - 接收去重后的 finding 列表
     - 逐条 Read 源码验证真实性
     - 标记 confirmed / false_positive / uncertain
         │
  ⑥ 主进程输出合并报告：
     ✅ Confirmed（N 条）
     ⚠️ Uncertain（N 条）
     ❌ False Positive（N 条）
     📊 各维度统计 + agent 覆盖度
```

## 与现有特性的兼容矩阵

| 特性 | 兼容 | 行为 |
|------|------|------|
| `--loop` | ✅ | 每轮并行，verifier 确认后写入 acceptedIssues |
| `--scope` | ✅ | scope 传给所有维度 agent |
| `--with` | ✅ | 参考文档传给所有维度 agent |
| `--rubric` | ⚠️ | 手动指定时禁用维度分离，所有 agent 用同一 rubric |
| `--quick` | ✅ | 跳过主进程评估，但 verifier 仍执行 |
| `--timeout` | ✅ | 每个 agent 独立超时控制 |

## 失败处理

| 场景 | 处理 |
|------|------|
| 某维度 agent 超时 | 跳过该维度，报告中标注 "security: 超时未完成" |
| 某维度 agent 输出无 JSON | 该维度降级为原始文本展示 |
| 全部 agent 失败 | 降级为串行模式重试一次 |
| verifier 失败 | 跳过验证步骤，原始结果标注 "未经 verifier 确认" |
| 某维度 agent 被安全拦截 | 同超时处理，记录到 errors |

## 成本估算

| 模式 | Token 倍数 | 典型耗时 |
|------|-----------|---------|
| 串行（当前） | 1× | 30-90s |
| --parallel 4 维 | 3-4× | 20-60s（并行瓶颈 = 最慢维度） |
| --parallel 2 维 | 1.5-2× | 15-45s |
| --parallel --loop ×3 轮 | 9-12× | 60-180s |

## 实施步骤

### Phase 1: 核心并行（最小可用）

1. SKILL.md 用法表加 `--parallel [维度列表]`
2. 主流程加步骤 ②-⑥（并行启动、收集、verifier、合并）
3. 并行启动用 Bash 后台任务（`run_in_background: true`），TaskOutput 收集结果
4. verifier prompt 模板

### Phase 2: 去重与降噪

1. file:line 精确匹配去重
2. desc 相似度去重（normalize 空白后 Jaccard > 0.7）
3. severity 冲突时取高

### Phase 3: 优化

1. 自适应路由（分析 diff 选维度）
2. 同维度对抗（`--parallel security --adversarial`）
3. 并行 loop（每轮并行 + 收敛判断改为跨维度）

## 不做的

- 多模型混合（Claude + GPT + Gemini）：增加外部依赖，review-cc-cli 定位是 Claude Code 生态工具
- 自动修复（`--fix`）：保持评审只读定位
- 持久化 agent team（Agent Teams API）：当前 API 稳定性不足，等成熟后再接入

## 风险

| 风险 | 缓解 |
|------|------|
| token 成本暴增 | 默认关闭，用户主动选择，文档明确标注成本 |
| 多 agent 对同一问题重复报告 | verifier 去重 |
| verifier 自身误判 | 不确定项标 uncertain 而非直接驳回 |
| 并发 Bash 任务资源竞争 | 最多 4 个并行 agent，不超过主机承载力 |
