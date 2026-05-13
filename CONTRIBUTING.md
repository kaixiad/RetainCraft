# 贡献指南

感谢您对 RetainCraft 项目的关注！我们欢迎各种形式的贡献。

## 如何贡献

### 报告问题

1. 使用 [GitHub Issues](https://github.com/kaixiad/RetainCraft/issues) 报告 bug
2. 提供详细的问题描述、复现步骤和环境信息
3. 包含相关的错误日志或截图

### 提交代码

1. Fork 本仓库
2. 创建您的特性分支：`git checkout -b feature/amazing-feature`
3. 提交您的更改：`git commit -m 'Add amazing feature'`
4. 推送到分支：`git push origin feature/amazing-feature`
5. 创建 Pull Request

### 代码规范

- 遵循 PEP 8 Python 代码规范
- 为新功能添加单元测试
- 更新相关文档
- 确保所有测试通过：`python -m pytest test_srs.py -v`

### 提交信息规范

使用清晰、描述性的提交信息：

```
feat: 添加新的学习方法支持
fix: 修复等级计算中的边界条件问题
docs: 更新API文档
test: 添加新的单元测试用例
refactor: 重构SM-2算法实现
```

## 开发环境设置

1. 克隆仓库：
```bash
git clone https://github.com/kaixiad/RetainCraft.git
cd retaincraft
```

2. 安装依赖（无外部依赖）：
```bash
# 项目仅使用Python标准库，无需额外安装
python --version  # 确保Python >= 3.10
```

3. 运行测试：
```bash
cd scripts
python -m pytest test_srs.py -v
```

## 项目结构

```
retaincraft/
├── SKILL.md                    # 主文件（执行清单 + 流程定义）
├── README.md                   # 项目说明
├── LICENSE                     # MIT 许可证
├── CONTRIBUTING.md             # 本文件
├── CHANGELOG.md                # 版本变更记录
├── requirements.txt            # Python 依赖
├── .github/
│   ├── workflows/ci.yml        # GitHub Actions CI/CD
│   ├── ISSUE_TEMPLATE/         # Issue 模板
│   └── pull_request_template.md # PR 模板
├── docs/
│   └── docu-review-report.md   # 文档审查报告
└── scripts/
    ├── srs.py                  # SM-2 间隔重复脚本
    ├── test_srs.py             # 单元测试（127 个用例）
    ├── scenarios.md            # 场景库示例
    ├── evidence.md             # 学术引用和效果量
    └── templates.md            # 输出格式模板
```

## 学术引用规范

如果您修改了学术引用相关内容，请确保：

1. 所有引用必须可溯源验证
2. 效果量数字必须与原始论文一致
3. 区分同行评审论文和博客文章
4. 标注引用来源类型（元分析、RCT、理论论文等）

## 行为准则

- 尊重所有参与者
- 接受建设性批评
- 专注于对社区最有利的事情
- 对他人表示同理心

## 许可证

通过贡献代码，您同意您的贡献将在 MIT 许可下发布。

## 联系方式

如有问题，请通过 GitHub Issues 联系我们。