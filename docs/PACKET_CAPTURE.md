# 抓包分析指南

本文档说明如何获取小红书 App 的 API 和签名算法。

## 准备工作

### 工具

| 工具 | 用途 | 下载 |
|------|------|------|
| **Proxyman** | macOS 抓包工具 | https://proxyman.io |
| **Charles** | 跨平台抓包工具 | https://www.charlesproxy.com |
| **mitmproxy** | 命令行抓包工具 | https://mitmproxy.org |

### 设备要求

- iPhone（已安装小红书 App）
- 电脑（与 iPhone 同一 Wi-Fi）

---

## Step 1: 安装证书

### Proxyman (macOS)

1. 打开 Proxyman → Certificate → Install on this Mac
2. 安装 iOS 证书：Certificate → Install on iOS Device → Simulator
3. 在 iPhone 上打开 `http://proxyman.io/ssl` 下载证书
4. 设置 → 通用 → 关于 → 证书信任设置 → 启用信任

### Charles (Windows/macOS)

1. Help → SSL Proxying → Install Charles Root Certificate
2. Help → SSL Proxying → Install Charles Root Certificate on a Mobile Device
3. 在 iPhone 浏览器打开 `chls.pro/ssl` 下载证书
4. 设置 → 通用 → 关于 → 证书信任设置 → 启用信任

---

## Step 2: 配置代理

1. 在电脑上启动抓包工具
2. 记下电脑的 IP 地址（如 `192.168.1.100`）和端口（默认 `8080`）
3. 在 iPhone 上：
   - 设置 → Wi-Fi → 点击当前网络 → 配置代理 → 手动
   - 服务器：电脑 IP
   - 端口：8080

---

## Step 3: 抓取请求

1. 在 iPhone 上打开小红书 App
2. 执行你想要分析的操作（如查看关注列表）
3. 在抓包工具中筛选 `xiaohongshu.com` 域名
4. 找到关键请求

### 关键 API 端点

| 功能 | 可能的端点 | 方法 |
|------|-----------|------|
| 关注列表 | `/api/sns/web/v1/user/following` | POST |
| 收藏列表 | `/api/sns/web/v1/note/collect/list` | POST |
| 点赞列表 | `/api/sns/web/v1/user/liked/notes` | POST |
| 关注用户 | `/api/sns/web/v1/user/follow` | POST |
| 取消关注 | `/api/sns/web/v1/user/unfollow` | POST |

---

## Step 4: 分析签名

### 查看请求头

重点关注以下请求头：

```
X-s: xxxxx          # 签名
X-t: 1700000000000  # 时间戳
X-Sign-Ver: 1       # 签名版本
X-Xs-Common: xxx    # 通用参数
```

### 分析步骤

1. **收集多个请求** - 同一操作多次请求，对比参数变化
2. **定位签名参数** - 找出哪些参数参与签名
3. **逆向签名算法** - 可能的方法：
   - JS 逆向（Web 端）
   - Frida hook（App 端）
   - 参考开源项目

---

## Step 5: 导出 Cookie

### 从抓包工具导出

1. 找到任意一个请求
2. 复制 Cookie 请求头的值
3. 格式类似：`web_session=xxx; a1=xxx; webId=xxx`

### 关键 Cookie 字段

| 字段 | 说明 |
|------|------|
| `web_session` | 会话标识 |
| `a1` | 设备指纹 |
| `webId` | Web 端 ID |
| `websectiga` | 安全 token |
| `sec_poison_id` | 防爬标识 |

---

## 注意事项

1. **Cookie 有效期** - Cookie 会过期，需要定期更新
2. **请求频率** - 不要请求太频繁，避免触发风控
3. **账号安全** - 使用小号测试，避免主号被封

---

## 参考资源

- [xiaohongshu-mcp](https://github.com/xpzouying/xiaohongshu-mcp) - 开源小红书 MCP 服务器
- [NolanHzy/novel](https://github.com/NolanHzy/novel) - 逆向分析参考
