"""配置模块 - 管理所有环境变量和配置"""

import os
import sys
from typing import List
from dotenv import load_dotenv

# 确保输出不被缓冲（Docker 容器中重要）
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# 加载环境变量
load_dotenv()


def parse_dates(date_str: str) -> List[str]:
    """解析日期字符串，支持逗号分隔的多个日期"""
    if not date_str:
        return []
    return [d.strip() for d in date_str.split(",") if d.strip()]


class Config:
    """应用配置"""
    
    # MIT Recreation 账号
    MIT_USERNAME: str = os.getenv("MIT_USERNAME", "")
    MIT_PASSWORD: str = os.getenv("MIT_PASSWORD", "")
    
    # 检测配置 - 支持多个日期，逗号分隔
    # 例如: "12/27/2025,12/28/2025,12/29/2025"
    _CHECK_DATES_RAW: str = os.getenv("CHECK_DATES", os.getenv("CHECK_DATE", "1/3/2026, 1/4/2026"))
    CHECK_DATES: List[str] = parse_dates(_CHECK_DATES_RAW)
    
    CHECK_INTERVAL_MIN: int = int(os.getenv("CHECK_INTERVAL_MIN", "30"))  # 0.5分钟
    CHECK_INTERVAL_MAX: int = int(os.getenv("CHECK_INTERVAL_MAX", "60"))  # 1分钟
    
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
        if not cls.CHECK_DATES:
            print("❌ 错误: 请设置 CHECK_DATES 环境变量")
            return False
        return True
    
    @classmethod
    def print_config(cls) -> None:
        """打印当前配置（隐藏敏感信息）"""
        print("=" * 60)
        print("🎾 MIT Tennis Court Availability Checker")
        print(f"📅 检测日期: {', '.join(cls.CHECK_DATES)} ({len(cls.CHECK_DATES)} 个日期)")
        print(f"⏱️  检测间隔: {cls.CHECK_INTERVAL_MIN // 60}-{cls.CHECK_INTERVAL_MAX // 60} 分钟")
        print(f"🖥️  Headless 模式: {cls.HEADLESS}")
        print(f"🔍 MIT_USERNAME: {'已设置' if cls.MIT_USERNAME else '❌ 未设置'}")
        print(f"🔍 MIT_PASSWORD: {'已设置' if cls.MIT_PASSWORD else '❌ 未设置'}")
        print(f"📱 Telegram: {'已配置' if cls.TELEGRAM_BOT_TOKEN and cls.TELEGRAM_CHAT_ID else '未配置'}")
        print("=" * 60)


# 导出单例配置
config = Config()

