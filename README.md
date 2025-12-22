# 🎾 MIT Tennis Court Availability Checker

自动检测 MIT Recreation 网球场空位并发送通知（支持 Telegram 推送）。

## 📁 项目结构

```
mit-tennis-notifier/
├── src/
│   ├── __init__.py      # 包初始化
│   ├── config.py        # 配置管理
│   ├── notifications.py # 通知（Telegram/桌面）
│   └── browser.py       # 浏览器操作
├── main.py              # 程序入口
├── Dockerfile           # Docker 配置
├── railway.toml         # Railway 部署配置
└── requirements.txt     # Python 依赖
```

## 🚀 快速开始

### 本地运行

1. **安装依赖**

```bash
pip install -r requirements.txt
playwright install firefox
```

2. **配置环境变量**

创建 `.env` 文件：

```bash
MIT_USERNAME=你的用户名
MIT_PASSWORD=你的密码
CHECK_DATE=12/22/2025

# 可选：Telegram 通知
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

3. **运行**

```bash
python main.py
```

### 云端部署 (Railway)

1. Fork 或 Push 到 GitHub
2. 在 [Railway](https://railway.app) 创建项目，连接仓库
3. 添加环境变量：
   - `MIT_USERNAME`
   - `MIT_PASSWORD`
   - `CHECK_DATE`
   - `HEADLESS=true`
   - `TELEGRAM_BOT_TOKEN` (推荐)
   - `TELEGRAM_CHAT_ID` (推荐)

## ⚙️ 配置说明

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `MIT_USERNAME` | MIT Recreation 用户名 | 必填 |
| `MIT_PASSWORD` | MIT Recreation 密码 | 必填 |
| `CHECK_DATE` | 要检测的日期 (MM/DD/YYYY) | `12/22/2025` |
| `CHECK_INTERVAL_MIN` | 最小检查间隔（秒） | `120` |
| `CHECK_INTERVAL_MAX` | 最大检查间隔（秒） | `240` |
| `HEADLESS` | 无头模式（云端必须为 true） | `false` |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token | 可选 |
| `TELEGRAM_CHAT_ID` | Telegram Chat ID | 可选 |

## 🔔 通知方式

### Telegram（推荐，云端必备）

1. 在 Telegram 找 [@BotFather](https://t.me/BotFather) 创建 Bot
2. 获取 Bot Token
3. 找 [@userinfobot](https://t.me/userinfobot) 获取你的 Chat ID
4. 设置环境变量

### 桌面通知（仅本地）

- **macOS**: 系统通知 + 语音提醒
- **Linux**: notify-send
- **Windows**: plyer

## 📢 通知逻辑

| 情况 | 行为 |
|------|------|
| 首次检测到空位 | ✅ 立即发送通知 |
| 可用时间有变化 | 🔄 发送更新通知 |
| 可用时间无变化 | 🔇 不重复通知 |
| 空位被抢完 | 😢 发送提醒 |

## 🐛 常见问题

**Q: 被 Cloudflare 阻止？**
A: 程序使用 Firefox 浏览器绕过检测，如果还是被阻止，建议本地运行。

**Q: 登录失败？**
A: 检查用户名密码是否正确，确保账号可以正常登录网站。

**Q: Railway 费用？**
A: 有 $5/月免费额度，此程序约消耗 $3-5/月。

## 📄 License

MIT
