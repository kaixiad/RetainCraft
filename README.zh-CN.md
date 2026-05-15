# 🧠 RetainCraft

[English](README.md) | [中文](README.zh-CN.md)

> 基于循证学习科学的 AI 辅助互动学习协议
> 整合间隔重复、主动回忆、费曼学习法、交错练习和精细加工提问 5 种科学方法
>
> *曾用名 "interactive-learning"*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 这是什么？

一个 [OpenClaw](https://github.com/openclaw) 技能，把 5 种科学验证的学习方法变成你和 AI 之间的互动系统。

不是"给你材料自己看"——而是 AI 和你一起学、一起练、追踪进度、在你遗忘前提醒你。

## 核心特性

- **5 种循证方法**整合在一个协议中：间隔重复（d=0.85）、主动回忆（d=0.74）、费曼学习法（d=0.54）、交错练习（d=0.47）、精细加工提问（d=0.56）——效果量均来自 [Donoghue & Hattie 2021](https://doi.org/10.3389/feduc.2021.581216) 元分析（242 项研究，16.9 万参与者）
- **SM-2 间隔重复**：自动计算复习间隔，不是固定时间表
- **摸底考试 + 模块测试**：学前学后对比，量化学习效果
- **倦怠检测**：连续答错自动降低难度或建议休息
- **搜索优先策略**：AI 回答问题前先搜索验证，标注来源
- **持久记忆**：学习数据跨会话保留
- **心跳集成**：到期复习自动提醒

## 环境要求

- Python >= 3.10
- 无外部依赖——仅使用 Python 标准库

> **Windows 用户**：如果没有 `python3`，请用 `python` 代替。

## 安装

```bash
# 从 ClawHub 安装
openclaw skills install retaincraft

# 手动安装
git clone https://github.com/kaixiad/RetainCraft.git ~/.openclaw/workspace/skills/retaincraft
```

## 使用方法

告诉你的 AI：
- "我想学线性代数"
- "教我贝叶斯定理"
- "帮我制定学习计划"

AI 会自动启动完整的学习流程。

## 文件结构

```
retaincraft/
├── SKILL.md                    # 主文件（执行清单 + 流程定义）
├── README.md                   # 英文说明
├── README.zh-CN.md             # 中文说明
├── LICENSE                     # MIT 许可证
├── CHANGELOG.md                # 版本变更记录
├── CONTRIBUTING.md             # 贡献指南
├── requirements.txt            # Python 版本要求
├── .github/
│   ├── workflows/ci.yml        # GitHub Actions CI/CD
│   ├── ISSUE_TEMPLATE/         # Issue 模板
│   └── pull_request_template.md # PR 模板
├── docs/
│   └── docu-review-report.md   # 文档审查报告
└── scripts/
    ├── srs.py                  # SM-2 间隔重复引擎 + 等级系统
    ├── test_srs.py             # 单元测试（133 个用例）
    ├── scenarios.md            # 模拟场景库（7 个场景）
    ├── evidence.md             # 学术引用和效果量
    └── templates.md            # 输出格式模板
```

## 数据存储

```
~/learn/
├── topics/{topic}/
│   ├── concepts.json           # 每个概念的 SM-2 状态
│   ├── notes.md                # 学习笔记
│   └── progress.md             # 掌握度追踪
├── test_history.json           # 模块测试历史
├── simulation_history.json     # 模拟历史
└── config.json                 # 学习偏好配置
```

## CLI 命令

```bash
# 核心命令
python3 scripts/srs.py init <topic>              # 创建主题
python3 scripts/srs.py add <topic> <concept>     # 添加概念
python3 scripts/srs.py review <topic>            # 开始复习会话（交互式）
python3 scripts/srs.py rate <topic> <concept> <rating>  # 评分概念（非交互式，给 AI 用）
python3 scripts/srs.py due                       # 查看今日到期复习
python3 scripts/srs.py status [topic]            # 查看整体 / 单主题状态

# 测试命令
python3 scripts/srs.py record-test <topic> <total> <correct>  # 记录模块测试结果
python3 scripts/srs.py test-history [topic]      # 查看测试历史
python3 scripts/srs.py record-simulation <topic> <scenario> <score> [--rounds N]  # 记录模拟结果
python3 scripts/srs.py simulation-history [topic]  # 查看模拟历史

# 画像命令
python3 scripts/srs.py profile                   # 查看用户画像
python3 scripts/srs.py profile --update          # 更新所有主题的画像
python3 scripts/srs.py profile --compare <job>   # 对比画像与职位要求

# 诊断命令
python3 scripts/srs.py check-session [topic]     # 检查未记录的测试
python3 scripts/srs.py check-burnout <topic>     # 分析倦怠风险

# 提醒命令
python3 scripts/srs.py setup-reminder            # 创建学习提醒和周报定时任务
python3 scripts/srs.py reminder                  # 生成今日学习计划
python3 scripts/srs.py weekly-report             # 生成周报数据
python3 scripts/srs.py check-reminder            # 检查提醒状态
python3 scripts/srs.py switch-channel            # 切换提醒通知渠道

# 配置
python3 scripts/srs.py config                    # 查看/设置配置
```

## 学术引用

| 方法 | 效果量 | 来源 |
|------|--------|------|
| 间隔重复 | d=0.85 | [Donoghue & Hattie 2021](https://doi.org/10.3389/feduc.2021.581216) |
| 主动回忆 | d=0.74 | Donoghue & Hattie 2021 |
| 精细加工提问 | d=0.56 | Donoghue & Hattie 2021 |
| 费曼学习法 / 自我解释 | d=0.54 | Donoghue & Hattie 2021 |
| 交错练习 | d=0.47 | Donoghue & Hattie 2021 |
| AI 辅导 | 0.63-1.3 SD | [Kestin et al. 2025](https://doi.org/10.1038/s41598-025-97652-6)（哈佛 RCT，N=194） |

> 所有 d 值均来自 Donoghue & Hattie (2021) 元分析（242 项研究，1,619 个效果量，169,179 名参与者）。Dunlosky et al. (2013) 使用定性分类（高/中/低效用），而非 Cohen's d。

## 已知限制

- **SM-2 算法**：经过验证但年代较久。FSRS（基于 ML 的现代替代方案）计划在未来版本中迁移。
- **尚无用户验证数据**：学习方法基于循证研究，但本实现尚未在真实用户中大规模验证。
- **费曼检验中的 AI 判断**：AI 评估你的解释是否正确，依赖底层 LLM 的准确性——关键知识请交叉验证权威来源。
- **单语言界面**：CLI 输出和文档主要为中文，英文界面支持已列入计划。

## 文档质量

本项目经过独立文档审查：

| 项目 | 状态 |
|------|------|
| 所有引用经溯源验证为真实 | ✅ |
| 效果量数值准确 | ✅ |
| 研究机构归属正确 | ✅ |
| 协议逻辑一致 | ✅ |
| 代码测试通过 | ✅ |
| 需要定制 | ⚠️ 通用模板——请根据你的背景调整 |

完整审查报告：`docs/docu-review-report.md`

## AI 辅助开发声明

本项目在 MiMo-v2.5-Pro、OpenClaw、WorkBuddy 和 CodeBuddy 的协助下开发。核心架构设计、学习方法选择、学术引用验证和代码审查由人工完成。AI 工具协助了代码生成、文档起草和文献搜索。所有 AI 生成的内容均已人工审查和验证。

## 许可证

MIT 许可证——自由使用、修改和分发。
