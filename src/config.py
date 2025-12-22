"""配置模块 - 管理所有环境变量和配置"""

import os
import sys
from dotenv import load_dotenv

# 确保输出不被缓冲（Docker 容器中重要）
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# 加载环境变量
load_dotenv()


class Config:
    """应用配置"""
    
    # MIT Recreation 账号
    MIT_USERNAME: str = os.getenv("MIT_USERNAME", "")
    MIT_PASSWORD: str = os.getenv("MIT_PASSWORD", "")
    
    # 检测配置
    CHECK_DATE: str = os.getenv("CHECK_DATE", "12/22/2025")
    CHECK_INTERVAL_MIN: int = int(os.getenv("CHECK_INTERVAL_MIN", "120"))  # 2分钟
    CHECK_INTERVAL_MAX: int = int(os.getenv("CHECK_INTERVAL_MAX", "240"))  # 4分钟
    
    # Telegram 配置 (可选)
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")
    
    # 运行模式
    HEADLESS: bool = os.getenv("HEADLESS", "false").lower() == "true"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # URL
    RESERVATION_URL: str = "https://mit.clubautomation.com/event/reserve-court-new"
    
    @classmethod
    def validate(cls) -> bool:
        """验证必要的配置是否已设置"""
        if not cls.MIT_USERNAME or not cls.MIT_PASSWORD:
            print("❌ 错误: 请设置 MIT_USERNAME 和 MIT_PASSWORD 环境变量")
            return False
        return True
    
    @classmethod
    def print_config(cls) -> None:
        """打印当前配置（隐藏敏感信息）"""
        print("=" * 60)
        print("🎾 MIT Tennis Court Availability Checker")
        print(f"📅 检测日期: {cls.CHECK_DATE}")
        print(f"⏱️  检测间隔: {cls.CHECK_INTERVAL_MIN // 60}-{cls.CHECK_INTERVAL_MAX // 60} 分钟")
        print(f"🖥️  Headless 模式: {cls.HEADLESS}")
        print(f"🔍 MIT_USERNAME: {'已设置' if cls.MIT_USERNAME else '❌ 未设置'}")
        print(f"🔍 MIT_PASSWORD: {'已设置' if cls.MIT_PASSWORD else '❌ 未设置'}")
        print(f"📱 Telegram: {'已配置' if cls.TELEGRAM_BOT_TOKEN and cls.TELEGRAM_CHAT_ID else '未配置'}")
        print("=" * 60)


# 导出单例配置
config = Config()

