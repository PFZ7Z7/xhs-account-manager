# 快速开始指南

## 安装

```bash
# 克隆仓库
git clone https://github.com/your-username/xhs-account-manager.git
cd xhs-account-manager

# 安装依赖
pip install -r requirements.txt
```

## 使用流程

### Step 1: 获取 Cookie

1. 参考 [抓包指南](docs/PACKET_CAPTURE.md) 设置抓包
2. 在 iPhone 上打开小红书 App
3. 在抓包工具中找到请求，复制 Cookie

### Step 2: 添加账号

```bash
python -m src.main account add
# 输入账号名称和 Cookie
```

### Step 3: 查看数据

```bash
# 列出账号
python -m src.main account list

# 查看关注列表
python -m src.main following list acc_xxx --limit 50

# 查看收藏列表
python -m src.main collection list acc_xxx --limit 50
```

### Step 4: 批量操作

```bash
# 批量取关
python -m src.main following unfollow acc_xxx --batch --count 10

# 批量取消收藏
python -m src.main collection uncollect acc_xxx --batch --count 10
```

### Step 5: 数据迁移

```bash
# 迁移关注到另一个账号
python -m src.main migrate following source_id target_id --count 100

# 迁移收藏
python -m src.main migrate collection source_id target_id --count 100
```

### Step 6: 数据备份

```bash
# 导出所有数据
python -m src.main backup export acc_xxx --output ./backup

# 导入数据
python -m src.main backup import acc_xxx followings_xxx.json --type following
```

## 注意事项

⚠️ **重要提醒**

1. **签名算法未实现** - 当前版本需要你通过逆向分析补充签名算法
2. **Cookie 会过期** - 需要定期更新 Cookie
3. **请求频率** - 不要请求太频繁，避免触发风控
4. **账号安全** - 建议使用小号测试

## 下一步

1. 阅读 [抓包指南](docs/PACKET_CAPTURE.md)
2. 分析小红书 API 签名算法
3. 更新 `src/api/signature.py` 中的签名实现
4. 测试功能

## 常见问题

### Q: 为什么请求失败？

A: 可能原因：
- Cookie 已过期
- 签名算法不正确
- 请求频率过高

### Q: 如何获取完整的关注列表？

A: 需要使用 App 端 API，参考抓包指南获取 App 端的 Cookie 和 API。

### Q: 数据存储在哪里？

A: 默认存储在 `data/xhs.db` SQLite 数据库中。
