# 版本变更记录

本文件记录 RetainCraft 的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本控制](https://semver.org/lang/zh-CN/)。

---

## [1.3.0] - 2026-05-17

**测试**: 159 个测试全部通过（+13）

### 新增

#### FSRS-5 间隔重复算法（默认）
- 基于 IEEE TKDE 2023 论文（Su, Ye, Nie, Cao & Chen）
- 自实现 ~120 行，保持零外部依赖
- 8 个核心函数：初始稳定性/难度、遗忘曲线、稳定性更新
- 19 个默认参数（FSRS_V5_WEIGHTS）
- 幂律遗忘曲线：R(t, S) = (1 + FACTOR × t / S)^DECAY
- 难度均值回归、Hard 惩罚、Easy 奖励
- 防御性工程：NaN/Inf 检查、值域 clamp、错误回退

#### 精确 Retrievability 计算
- R 从近似值 0.9 升级为精确计算：R(t, S) = (1 + FACTOR × elapsed / S)^DECAY
- elapsed = today - (next_review - interval_days)
- 同天 review 正确得到 R≈1.0，逾期 review 正确得到 R<0.9

#### config algorithm 切换
- `srs.py config set algorithm fsrs` — 启用 FSRS-5（默认）
- `srs.py config set algorithm sm2` — 使用 SM-2（备选）
- 向后兼容：旧数据自动初始化 FSRS 字段

#### 4 个新命令
- `today` — 今日学习计划，含逾期分析和建议
- `streak` — 连续学习天数（Duolingo 模型：从今天算）
- `analyze` — 学习趋势分析、薄弱概念、活动统计
- `optimize-params` — 基于本地 review 历史优化 FSRS-5 参数
  - 数值梯度下降（有限差分），纯 Python 实现
  - 需 1000+ 次 review，检查评分分布和参数漂移
  - 参考 FSRS 社区最佳实践

#### 个性化参数支持
- `config.fsrs_weights` — 存储优化后的 19 个参数
- `FSRS_V5_WEIGHTS_DEFAULT` — 不可变默认值
- `FSRS_V5_WEIGHTS` — 可个性化

#### 学习模板
- `learning-templates.json` — 3 个模板（编程语言、外语学习、考试复习）

### 重构

#### main() 函数重构
- 246 行 if-elif → 38 行 dispatch 字典（O(1) 查表）
- 所有 cmd_* 函数统一签名为 `(args: list[str])`
- 7 个新 cmd_* 函数从 main() 内联逻辑提取

#### 超长函数拆分（全部 < 50 行）
- `cmd_review` (94→39), `check_burnout` (88→42)
- `calc_level_by_accuracy` (84→38), `cmd_status` (74→23)

#### 魔法数字提取
- `SM2_SECOND_INTERVAL = 6` 替换硬编码

### 修复

- **FSRS rating 映射**：`"again"` 改为 `"wrong"`，匹配系统实际使用的评分
- **FSRS 遗忘路径**：`rating == "again"` 改为 `rating_int == 1`
- **FSRS 稳定性永不增加**：R 从 1.0 改为精确计算
- **cmd_analyze 缺少 ensure_dirs()**：新用户首次运行不再崩溃
- **R12 作者归属**：Su, J. 为第一作者（非 Ye, J.）
- **帮助文本**：补充 today/streak/analyze/optimize-params 命令

### 新增学术引用

| # | 引用 | 用途 |
|---|------|------|
| R12 | Su, Ye, Nie, Cao & Chen (2023) — FSRS-5 IEEE TKDE | FSRS-5 实现 |
| R13 | fsrs-rs 工程实践 | 技术参考 |

### 文档更新
- `SKILL.md` 版本 1.3.0，FSRS-5 默认标注
- `README.md` / `README.zh-CN.md` — 23 个命令、FSRS-5 默认、optimize-params
- `evidence.md` R12、R13（作者归属修正）
- `CONTRIBUTING.md` — 测试数 159、文件结构更新

---

## [1.2.0] - 2026-05-15

**测试**: 146 个测试全部通过

### 新增

#### 提醒系统（5 个新命令）
- `setup-reminder` — 创建学习提醒和周报 cron 任务，自动检测通知渠道
- `reminder` — 生成今日学习计划，包含基于 Ebbinghaus 遗忘曲线的风险分析
- `weekly-report` — 生成周报数据，包含掌握性经验和倦怠检测
- `check-reminder` — 检查提醒和周报的启用状态
- `switch-channel` — 交互式切换提醒通知渠道，自动重建 cron 任务

#### 学习契约（Step 0.1）
- 基于 Gollwitzer (1999) 实施意图理论
- "如果 X 情况发生，我会做 Y 行动" 格式
- 帮助用户制定具体、可执行的学习计划

#### 遗忘风险提醒
- 基于 Ebbinghaus (1885) 遗忘曲线（Murre & Dros 2015 验证）
- 根据距离上次学习的天数，动态计算遗忘风险等级
- 7 天未学习 → 知识基本回到起点

#### 学习日志收集
- 新增 `learning_log.json` 自动记录所有学习活动
- 支持周报生成和学习趋势分析

### 修复

#### SM-2 第二次间隔修复
- **问题**: 第二次复习间隔计算为 `1 × 2.5 = 2.5 天`（取整为 2 天）
- **正确值**: 原始 SM-2 算法规定第二次间隔为 **6 天**（Wozniak, 1987）
- **修复**: 第二次复习（`reviews==1`）时直接设为 6 天

#### 其他修复
- JSON 解析兼容性（适配 OpenClaw 不同版本）
- iterdir() 安全性（3 处缺少 ensure_dirs()）
- setup-reminder 会话类型（改为 isolated + announce）
- 降级逻辑（while 循环改为单次 if 判断）
- 代码质量：时间格式验证、PEP 8 规范化

### 新增学术引用

| # | 引用 | 用途 |
|---|------|------|
| R7 | Gollwitzer (1999) — 实施意图理论 | 学习契约 |
| R8 | Maslach & Leiter (2016) — 倦怠理论 | 懈怠响应策略 |
| R9 | Steel (2007) — 拖延心理元分析 | 遗忘风险提醒 |
| R10 | Ebbinghaus (1885) — 遗忘曲线 | 遗忘风险提醒 |
| R11 | Bandura (1997) — 自我效能感 | 周报鼓励语 |

---

## [1.1.0] - 2026-05-13

### 新增
- `check-session [topic]` 命令：检测未记录的模块测试
- `check-burnout <topic> [--window N]` 命令：分析学习倦怠风险
- Session Checkpoint 机制：每个 Phase 结束时强制状态保存自检清单
- 13 个新测试用例（127 个总计）

### 变更
- 项目重命名为 RetainCraft（原 interactive-learning）
- MIT 许可证、CONTRIBUTING.md、CHANGELOG.md
- GitHub Actions CI/CD（Python 3.10/3.11/3.12 矩阵测试）
- 新增 sanitize_concept()、_atomic_text_save()
- 46 个新测试（114 个总计）

---

## [1.0.0] - 2026-05-06

### 新增
- 初始版本发布
- 5 种循证学习方法：间隔重复、主动回忆、费曼学习法、交错练习、精细加工提问
- SM-2 间隔重复算法实现
- 等级系统（L1-L5）和升降级规则
- 68 个单元测试用例

### 学术引用
- Donoghue & Hattie (2021) 元分析
- Kestin et al. (2025) 哈佛 RCT
- Ericsson et al. (1993) 刻意练习
- SM-2 算法 (Wozniak, 1987)

---

## 版本说明

- **新增**：新功能
- **修复**：Bug 修复
- **重构**：代码重构
- **优化**：性能改进

---

**维护者**：kaixiad
**许可证**：MIT License
