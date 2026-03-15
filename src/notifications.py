"""通知模块 - 管理 Telegram 和桌面通知"""

import platform
import subprocess
import urllib.request
import urllib.parse
from typing import Optional

from .config import config


def send_telegram(message: str) -> bool:
    """
    发送 Telegram 消息
    
    Args:
        message: 要发送的消息（支持 HTML 格式）
        
    Returns:
        是否发送成功
    """
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        if config.DEBUG:
            print("⚠️ Telegram 未配置，跳过发送")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
        data = urllib.parse.urlencode({
            "chat_id": config.TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }).encode()
        
        req = urllib.request.Request(url, data=data)
        urllib.request.urlopen(req, timeout=10)
        print("📱 Telegram 通知已发送!")
        return True
    except Exception as e:
        print(f"⚠️ Telegram 发送失败: {e}")
        return False


def send_desktop_notification(title: str, message: str) -> bool:
    """
    发送桌面通知（仅在非 headless 模式下有效）
    
    Args:
        title: 通知标题
        message: 通知内容
        
    Returns:
        是否发送成功
    """
    if config.HEADLESS:
        return False
    
    system = platform.system()
    
    try:
        if system == "Darwin":  # macOS
            script = f'display notification "{message}" with title "{title}" sound name "Glass"'
            subprocess.run(["osascript", "-e", script])
            subprocess.run(["say", f"Good news! Tennis court available on {', '.join(config.CHECK_DATES)}"])
            return True
        elif system == "Linux":
            result = subprocess.run(["notify-send", title, message], check=False)
            return result.returncode == 0
        elif system == "Windows":
            try:
                from plyer import notification
                notification.notify(title=title, message=message, timeout=10)
                return True
            except ImportError:
                print("⚠️ Windows 通知需要安装 plyer: pip install plyer")
                return False
    except Exception as e:
        print(f"⚠️ 桌面通知失败: {e}")
        return False
    
    return False


def send_notification(title: str, message: str) -> None:
    """
    发送通知（自动选择可用的通知方式）
    
    Args:
        title: 通知标题
        message: 通知内容
    """
    # 尝试桌面通知
    send_desktop_notification(title, message)
    
    # 发送 Telegram 通知
    telegram_msg = (
        f"🎾 <b>{title}</b>\n\n"
        f"{message}\n\n"
        f"🔗 <a href='{config.RESERVATION_URL}'>立即预订</a>"
    )
    send_telegram(telegram_msg)
    
    # 控制台输出
    print(f"\n{'=' * 60}")
    print(f"🎾 {title}")
    print(f"📅 {message}")
    print(f"{'=' * 60}\n")

