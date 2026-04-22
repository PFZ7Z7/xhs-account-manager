# XHS Account Manager

小红书账号管理工具 - 基于 Cookie 的批量操作与数据迁移

## 功能特性

- ✅ 多账号 Cookie 管理
- ✅ 批量取关
- ✅ 批量收藏迁移
- ✅ 数据备份（关注/收藏/点赞）
- ✅ 账号间数据迁移

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 配置账号
python src/main.py account add

# 查看关注列表
python src/main.py following list

# 批量取关
python src/main.py following unfatch --batch

# 数据备份
python src/main.py backup --all
```

## 项目结构

```
xhs-account-manager/
├── src/
│   ├── api/          # API 客户端
│   ├── core/         # 核心逻辑
│   ├── models/       # 数据模型
│   └── utils/        # 工具函数
├── tests/            # 测试
├── docs/             # 文档
├── scripts/          # 脚本
├── config/           # 配置
└── data/             # 数据存储
```

## 开发状态

详见 [PROJECT_PLAN.md](PROJECT_PLAN.md)
