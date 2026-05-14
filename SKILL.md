---
name: retaincraft
description: >
  Evidence-based AI-assisted learning protocol combining spaced repetition (SM-2),
  active recall, Feynman technique, interleaving, and deliberate practice.
  Features pre-assessment, burnout detection, progress tracking, and system memory integration.
  基于循证学习科学的 AI 辅助互动学习协议，整合间隔重复、主动回忆、费曼学习法、
  交错练习和精细加工提问 5 种科学方法。
version: 1.1.0
author: kaixiad
license: MIT
homepage: https://github.com/kaixiad/RetainCraft
tags:
  - learning
  - education
  - study
  - tutoring
  - ai-tutor
  - ai-learning
  - spaced-repetition
  - active-recall
  - feynman-technique
  - interleaving
  - evidence-based
  - learning-protocol
  - level-system
  - progress-tracking
  - burnout-detection
  - openclaw
  - 学习
  - 教育
  - AI学习
  - AI辅导
  - 间隔重复
  - 主动回忆
  - 费曼学习法
  - 交错练习
  - 循证学习
  - 学习协议
metadata:
  openclaw:
    emoji: "📚"
    requires:
      bins:
        - python3
    os:
      - darwin
      - linux
      - win32
    always: false
---

# RetainCraft

> 基于循证学习科学的 AI 辅助互动学习协议
> 结合 5 种科学验证方法 + 自我评价 + 摸底考试 + 定制化学习路径
>
> 📖 **详细流程说明**: [references/full-workflow.md](references/full-workflow.md)

---

## ⚠️ 执行清单(每次学习开始前必须读)

### 关键执行步骤(不可违反)

1. **模块测试结束后必须执行**:
   ```bash
   python3 scripts/srs.py record-test <topic> <total> <correct>
   ```
   不执行此命令 = 模块测试无效,等级不更新。

2. **费曼检验(L5 必需)**:
   - L5 精通需要:连续 2 次模块测试答对率 >=90% + 费曼检验通过
   - 费曼检验:AI助手扮演"不懂的学生",追问 3 个问题
   - 用户全部答对 → L5 确认
   - 用户答错 → L4 保持
   > **注**:费曼检验是 AI 助手执行的附加验证流程,不在 srs.py 代码中强制执行。

3. **评分纪律(不可违反)**:
   - 评分标准在测试开始前公布,测试过程中不可修改
   - 单题得分 >= 7 分 → 算"答对"
   - 不可因用户质疑而改分

4. **逐级升级限制**:
   - 等级只能逐级升级,不能跳级
   - 每次升级需要连续 2 次达标

---

## 📚 核心方法论(循证)

| 方法 | 效果量 | 来源 |
|------|--------|------|
| 间隔重复 | d=0.85 | Donoghue & Hattie 2021 元分析 |
| 主动回忆 | d=0.74 | Donoghue & Hattie 2021 元分析 |
| 交错练习 | d=0.47 | Donoghue & Hattie 2021 元分析 |
| 精细加工提问 | d=0.56 | Donoghue & Hattie 2021 元分析 |
| 费曼学习法 | d=0.54* | Donoghue & Hattie 2021 元分析 |
| AI 辅导 | 0.63-1.3 SD | Kestin et al. 2025 RCT |

> **注**: *d=0.54 对应原文"自我解释"，此处映射为费曼学习法。
> **参考**: scripts/evidence.md(详细引用和效果量)

---

## 🔄 完整流程:五步启动

### Step 0:学习意愿评估
- 用户完成自我评估问卷(主题、目标、水平、时间、偏好)

### Step 0.5:预习材料(零基础专用)
- 触发条件:用户自评"完全零基础"
- AI助手搜索入门资料,精炼成"快速概览"(800-1500 字)

### Step 1:摸底考试
- 5-8 道题,覆盖基础到进阶
- ⚠️ 摸底考试不调用 record-test，不写入 test_history

### Step 2:学习路径定制
- Step 2a:行业调研(web_search 搜索学习路线、岗位要求)
- Step 2b:路径生成(3-8 个模块，含学习目标、知识点、验收标准)
- Step 2c:用户确认后开始学习

### Step 3-4:学习循环 + 间隔复习
- 详见 [references/full-workflow.md](references/full-workflow.md)

---

## 📊 等级系统(L1-L5)

### 等级标准

| 等级 | 标准 | 行为特征 |
|------|------|----------|
| 🔴 L1 入门 | 无测试记录或首次 <20% | 从零开始 |
| 🟠 L2 初学 | 首次 >=20% | 有概念但不系统 |
| 🟡 L3 进阶 | 连续 2 次 >=40% | 能独立应用 |
| 🟢 L4 熟练 | 连续 2 次 >=70% | 能解决复杂问题 |
| 🔵 L5 精通 | 连续 2 次 >=90% + 费曼检验 | 能教会别人 |

### 升降级规则
- 升级:连续 2 次达标(不能跳级)
- 降级:连续 3 次不达标(最低降到 L2)

### 两个独立维度
- **等级** = 基于模块测试答对率(权威)
- **SM-2 状态** = 基于概念 mastered 比例(仅展示)

---

## 🔄 学习循环(每模块)

### Phase 0:框架搭建(10-15 min)
- AI助手提问,引导发现核心概念

### Phase 1:主动输入(25-40 min)
- 用户学习原始材料,每 15 分钟暂停回忆

### Phase 2:费曼检验(15-20 min)
- 用户向 AI助手解释所学,AI扮演"不懂的学生"追问

### Phase 2.5:实战模拟(15-20 min)
- 推荐 2-3 个模拟场景,用户选择后执行 3-5 轮
- 按 5 维度打分(100分)，见 scripts/scenarios.md

### Phase 3:测试巩固(15-20 min)
- 5-8 道混合题型测试
- ⚠️ 必须判定"复习"还是"模块测试"

| 项目 | 复习 | 模块测试 |
|------|------|----------|
| 目的 | 强化记忆 | 阶段性评估 |
| 影响 | 不影响等级 | 决定等级升降 |
| 命令 | srs.py rate | srs.py record-test |

### Phase 4:间隔复习(SM-2 算法)
- 基于 SM-2 时间表，到期主动提醒
- 心跳检查: `python3 scripts/srs.py due`

---

## ⚠️ 倦怠检测

**触发条件(任一)**:
- 连续答错 3 题以上
- 连续 2 次测试分数下降
- 用户主动说"累了""不想学了"

**响应**:降低难度、建议休息、切换轻松模式

---

## 🤖 AI助手行为规范

### ✅ 应该做的
- 用户问问题 → 先反问"你是怎么想的?"
- 用户卡住 → 给提示(不是答案)
- 用户答对 → 确认 + 追问"为什么是这样?"
- **每次回答知识性问题前 → 先 web_search 验证**
- **等级变化时必须主动告知用户**

### ❌ 不应该做的
- 直接给完整答案(除非用户明确要求)
- 测试后只打分不解析
- 用户疲劳时继续高强度

---

## 🔍 搜索优先规则

**铁律:AI助手回答任何知识性问题前,必须先搜索验证。**

| 场景 | 必须搜索? |
|------|-----------|
| 用户问"XX 是什么" | ✅ |
| 出测试题的正确答案 | ✅ |
| 费曼检验时判断用户对错 | ✅ |
| 规划学习路径 | ✅ |
| 流程性对话 | ❌ |

**规则**:事实性陈述必须附来源链接，不确定就说"我不确定,让我查一下"

---

## 🔒 Session Checkpoint 机制

### Phase 完成自检(每个 Phase 结束时必须执行)
```
□ 当前 Phase 的核心产出是否已完成?
□ 如果模块测试:是否已调用 record-test?
□ 是否已将关键进展写入 memory/?
```

### 违检检测命令
```bash
python3 scripts/srs.py check-session [topic]  # 检测未记录的测试
python3 scripts/srs.py check-burnout <topic>   # 分析倦怠风险
```

---

## 🧠 记忆持久化方案

### 双系统分工

| 系统 | 存什么 | 位置 |
|------|--------|------|
| **系统 memory** | 学习进度摘要、薄弱点 | `memory/YYYY-MM-DD.md` |
| **~/learn/** | SM-2 算法数据、概念掌握度 | `~/learn/topics/{topic}/concepts.json` |

### 恢复优先级
concepts.json > memory 文件

---

## 💓 复习提醒(Heartbeat 集成)

```
AI助手收到心跳 → python3 scripts/srs.py due → 有到期内容 → 通知用户
```

---

## ⚙️ 配置系统

```
~/learn/config.json
{
  "learning_depth": "standard",    // shallow / standard / deep
  "learner_type": "practical",     // visual / practical / theoretical
  "daily_review_limit": 20,
  "session_duration": 60,
  "burnout_threshold": 3,
  "mastery_threshold": 0.8,
  "level_thresholds": { "L2": 0.2, "L3": 0.4, "L4": 0.7, "L5": 0.9 }
}
```

---

## 📚 参考材料

- **完整流程说明**: references/full-workflow.md
- **场景库示例**: scripts/scenarios.md
- **学术引用和效果量**: scripts/evidence.md
- **等级判定算法**: scripts/srs.py(源码为准)
- **输出格式模板**: scripts/templates.md

---

## 🎯 多主题支持

| 优先级 | 描述 | 示例 |
|--------|------|------|
| 1-紧急 | 截止日期临近 | 期末考试、面试准备 |
| 2-重要 | 核心技能 | 编程语言、专业认证 |
| 3-常规 | 日常学习 | 新技术、爱好 |
| 4-扩展 | 拓宽视野 | 相关领域、软技能 |
| 5-储备 | 未来可能用到 | 待学习清单 |

- 最多同时进行 3 个主题
- 每个主题独立的 concepts.json 和 test_history
- 复习可以跨主题（交错练习）
