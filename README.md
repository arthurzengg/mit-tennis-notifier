# 🎾 MIT Tennis Court Availability Checker

自动检测 MIT Recreation 网球场空位并发送桌面通知。

## 🚀 快速开始

### 1. 安装依赖

```bash
uv sync
uv run playwright install chromium
```

或者使用 pip：
```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. 配置账号

复制 `.env.example` 为 `.env` 并填写你的 MIT Recreation 账号信息：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```
MIT_USERNAME=你的用户名
MIT_PASSWORD=你的密码
CHECK_DATE=12/27/2025
CHECK_INTERVAL_SECONDS=300
```

### 3. 运行

```bash
uv run python tennis_checker.py
```

或者直接：
```bash
python tennis_checker.py
```

## ⚙️ 配置说明

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `MIT_USERNAME` | MIT Recreation 用户名 | 必填 |
| `MIT_PASSWORD` | MIT Recreation 密码 | 必填 |
| `CHECK_DATE` | 要检测的日期 | `12/27/2025` |
| `CHECK_INTERVAL_SECONDS` | 检查间隔（秒） | `300` (5分钟) |

## 🔔 通知方式

- **macOS**: 桌面通知 + 语音提醒
- **Linux**: 桌面通知 (notify-send)
- **Windows**: 桌面通知 (plyer)

## 📝 注意事项

1. 首次运行会自动下载 Chrome 驱动
2. 默认会打开浏览器窗口，如果想后台运行，可以在代码中取消 `--headless` 注释
3. 按 `Ctrl+C` 可以停止程序
4. 建议将检查间隔设置为 5 分钟以上，避免对服务器造成压力

## 🐛 常见问题

**Q: 提示登录失败？**
A: 检查用户名密码是否正确，也可能是网站更新了登录页面结构

**Q: 检测不到空位？**
A: 网站结构可能有变化，可以手动打开浏览器观察

**Q: Chrome 驱动下载失败？**
A: 确保网络连接正常，或手动安装 ChromeDriver

