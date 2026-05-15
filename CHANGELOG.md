# 版本变更记录

本文件记录 RetainCraft 的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本控制](https://semver.org/lang/zh-CN/)。

## [1.2.0] - 2026-05-15

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
- **来源**: https://www.super-memory.com/english/ol/sm2.htm

#### JSON 解析兼容性修复
- `_cron_exists()` 和 `_get_user_channel()` 适配 OpenClaw 不同版本的 JSON 输出格式
- 新版本返回 `{"jobs": [...]}` 结构，旧版本返回数组
- 修复后新旧版本通用

#### iterdir() 安全性修复
- 修复 3 处 `TOPICS_DIR.iterdir()` 缺少 `ensure_dirs()` 调用
- 影响命令: `cmd_reminder`、`profile --update`、`cmd_weekly_report`
- 修复后新用户首次运行不再崩溃

#### setup-reminder 会话类型修复
- **问题**: 每日提醒使用 `--session main` + `--message`，但 OpenClaw 对 main session 要求 `--system-event`
- **修复**: 改为 `--session isolated` + `--announce`（与周报一致）
- **影响**: 每日提醒 cron 创建失败或投递行为异常

#### 降级逻辑修复（渐进降级）
- **问题**: while 循环用同一组 3 次测试连续降多级（L5→L2）
- **正确行为**: 每次检查只降一级，下次新测试结果再决定是否继续降
- **科学依据**: SM-2 算法答错只重置 interval 不跳阶段；Ebbinghaus 遗忘曲线是连续函数
- **修复**: while 循环改为单次 if 判断

#### 代码质量改进
- `cmd_setup_reminder` 添加 HH:MM 时间格式验证
- `record-simulation` 现在记录到 `learning_log.json`，周报包含模拟数据
- PEP 8 规范化：12 处顶层函数间空行修正

### 新增学术引用（5 篇）

| # | 引用 | 用途 |
|---|------|------|
| R7 | Gollwitzer (1999) — 实施意图理论 | 学习契约 |
| R8 | Maslach & Leiter (2016) — 倦怠理论 | 懈怠响应策略 |
| R9 | Steel (2007) — 拖延心理元分析 | 遗忘风险提醒 |
| R10 | Ebbinghaus (1885) — 遗忘曲线 | 遗忘风险提醒 |
| R11 | Bandura (1997) — 自我效能感 | 周报鼓励语 |

所有引用均经过溯源验证，详见 `scripts/evidence.md`。

### 文档更新

- `CHANGELOG.md` — v1.2.0 完整变更日志
- `README.md` / `README.zh-CN.md` — CLI 命令列表更新（11 → 18 个命令）
- `SKILL.md` — 版本号更新，新增执行清单第 5-8 条，学习契约（Step 0.1）
- `evidence.md` — 新增 5 篇引用的详细溯源信息
- `docu-review-report.md` — 新增 R7-R11 溯源验证，SM-2 参数修正

---

## [1.1.0] - 2026-05-13

### 新增
- `check-session [topic]` 命令：检测未记录的模块测试，防止 AI 遗忘导致等级不更新
- `check-burnout <topic> [--window N]` 命令：分析学习倦怠风险，返回趋势和休息建议
- Session Checkpoint 机制：每个 Phase 结束时强制状态保存自检清单
- 恢复流程新增 check-session 步骤：启动时验证上次 session 是否正常关闭
- 13 个新测试用例（127 个总计），覆盖 check-session 和 check-burnout

### 变更
- 项目重命名为 RetainCraft（原 interactive-learning）
- SKILL.md tags 优化：新增 evidence-based、ai-tutor、study-protocol、interleaving、level-system、费曼学习法、AI辅导、循证学习
- SKILL.md Phase 4 SM-2 公式歧义修复：hard/easy 公式补充"同时"连接词
- docu-review-report 行号引用改为章节引用，避免版本漂移
- docu-review-report 更新修复状态（升级阈值符号、费曼检验评分、SM-2 公式）

### 新增
- 添加 MIT 许可证文件
- 创建 requirements.txt 声明 Python 版本要求
- 添加 CONTRIBUTING.md 贡献指南
- 添加 CHANGELOG.md 版本变更记录
- 添加 GitHub Actions CI/CD 工作流（.github/workflows/ci.yml），支持 Python 3.10/3.11/3.12 矩阵测试
- 添加 GitHub Issue 模板（Bug 报告 + 功能请求）
- 添加 Pull Request 模板
- 新增 `sanitize_concept()` 函数，为 concept_name 提供输入验证（防御纵深）
- 新增 `_atomic_text_save()` 函数，防止文本文件写入中断导致数据损坏
- 新增 46 个单元测试用例（114 个总计），覆盖 sanitize_concept、_atomic_text_save、save_progress、simulation 边界等

### 修复
- 修正 README.md 中的学术引用错误（主动回忆来源）
- 统一 AI 辅导效果量描述格式
- 统一 srs.py 错误消息为英文（原中英文混杂），提升国际化兼容性
- SKILL.md Phase 4 SM-2 描述：区分 good/hard/easy/wrong 四种评分公式（原仅描述 good）
- SKILL.md 明确费曼检验为 AI 助手执行的附加验证流程，不在 srs.py 代码中强制执行
- evidence.md 学术引用溯源：将 Wang & Srivastava (2025) 博客文章替换为原始研究论文 Wang et al. (2024) Tutor CoPilot (arXiv:2410.03017)，提升引用规范性

### 优化
- 完善文档结构，符合开源项目标准
- 为所有函数添加类型提示和文档字符串
- 优化配置加载机制，添加缓存功能
- 改进输入验证和错误处理
- 提升代码可读性和可维护性
- SKILL.md config.json示例补充level_thresholds配置
- SKILL.md Phase 2.5明确评分维度引用scenarios.md
- 将"方案质量审计"章节从SKILL.md移入README.md
- Step 0.5补充输出格式、字数上限和用户确认步骤
- 更新README中srs.py行数和测试用例数
- 将draft-section2.md移至docs/目录
- 删除SKILL.md通用评分维度表格，统一引用scenarios.md
- 补充费曼学习法与自我解释的认知机制差异说明
- 统一L1→L2升级规则为"前2次测试平均>=20%"
- 明确降级最低到L2的设计决策
- 提取overdue计算为公共函数，添加畸形日期防护
- 补充calc_overdue函数的边界测试用例
- `save_progress()` 改用原子写入模式，防止进程中断导致数据损坏
- `cmd_add()` 和 `cmd_rate()` 均对 concept_name 进行输入验证
- 测试从 monkey-patch 迁移到 unittest.mock.patch，提升测试代码规范性

## [1.0.0] - 2026-05-06

### 新增
- 初始版本发布
- 基于循证学习科学的 AI 辅助互动学习协议
- 5 种科学验证学习方法整合：
  - 间隔重复（SM-2 算法）
  - 主动回忆
  - 费曼学习法/自我解释
  - 交错练习
  - 精细加工提问
- SM-2 间隔重复算法实现
- 等级系统（L1-L5）和升降级规则
- 摸底考试和学后测试
- 倦怠检测机制
- 搜索优先防幻觉机制
- 记忆持久化方案
- Heartbeat 集成复习提醒
- 多主题支持和优先级队列
- 实战模拟场景库
- 完整的 CLI 工具（srs.py）
- 68 个单元测试用例

### 技术细节
- Python 标准库实现，无外部依赖
- 跨平台支持（Windows/macOS/Linux）
- JSON 数据存储格式
- 模块化设计，易于扩展

### 学术引用
- Donoghue & Hattie (2021) 元分析 - 5 项核心效果量
- Kestin et al. (2025) 哈佛 RCT - AI 辅导效果
- Ericsson et al. (1993) - 刻意练习理论
- SM-2 算法 (Wozniak, 1987) - 间隔重复实现

---

## 版本说明

- **新增**：新功能
- **修复**：Bug 修复
- **优化**：性能改进或代码重构
- **废弃**：即将移除的功能
- **移除**：已移除的功能
- **安全**：安全相关的修复

---

**维护者**：kaixiad
**许可证**：MIT License