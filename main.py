#!/usr/bin/env python3
"""
MIT Tennis Court Availability Checker
主入口点
"""

import time
import random
from datetime import datetime

from src.config import config
from src.browser import TennisBrowser
from src.notifications import send_notification


def run_checker():
    """运行网球场空位检测"""
    
    # 打印配置信息
    config.print_config()
    
    # 验证配置
    if not config.validate():
        time.sleep(5)
        return
    
    # 初始化浏览器
    browser = TennisBrowser()
    
    if not browser.start():
        print("❌ 无法启动浏览器，退出程序")
        return
    
    try:
        # 登录
        if not browser.login():
            print("❌ 登录失败，退出程序")
            return
        
        check_count = 0
        last_available_times = None
        consecutive_errors = 0
        max_consecutive_errors = 3
        
        # 主循环
        while True:
            check_count += 1
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n[{current_time}] 第 {check_count} 次检查...")
            
            # 检查浏览器是否还活着
            if not browser.is_alive():
                print("⚠️ 检测到浏览器已关闭，正在重启...")
                if not browser.restart():
                    print("❌ 重启浏览器失败，等待后重试...")
                    time.sleep(30)
                    continue
                consecutive_errors = 0
            
            available, current_times = browser.check_availability()
            
            # 检查是否有错误（空结果可能是正常的，也可能是错误）
            # 这里通过连续错误计数来判断
            if not available and not current_times:
                # 可能是真的没有空位，也可能是出错了
                # 通过检查浏览器状态来判断
                if not browser.is_alive():
                    consecutive_errors += 1
                    print(f"⚠️ 检测到错误 ({consecutive_errors}/{max_consecutive_errors})")
                    if consecutive_errors >= max_consecutive_errors:
                        print("🔄 连续错误过多，重启浏览器...")
                        if browser.restart():
                            consecutive_errors = 0
                        else:
                            print("❌ 重启失败，等待后重试...")
                            time.sleep(30)
                    continue
            else:
                consecutive_errors = 0  # 重置错误计数
            
            if available:
                times_str = ", ".join(current_times)
                
                if last_available_times is None:
                    # 首次检测到空位
                    send_notification(
                        "🎾 MIT网球场有空位!",
                        f"日期: {config.CHECK_DATE}\n可用时间: {times_str}\n快去预订!"
                    )
                    print("\n🎉 检测到空位！程序将继续运行以持续监控...")
                    
                elif set(current_times) != set(last_available_times):
                    # 可用时间有变化
                    new_times = set(current_times) - set(last_available_times)
                    removed_times = set(last_available_times) - set(current_times)
                    
                    change_info = []
                    if new_times:
                        change_info.append(f"🆕 新增: {', '.join(sorted(new_times))}")
                    if removed_times:
                        change_info.append(f"❌ 已无: {', '.join(sorted(removed_times))}")
                    
                    send_notification(
                        "🔄 MIT网球场时间更新!",
                        f"日期: {config.CHECK_DATE}\n当前可用: {times_str}\n{chr(10).join(change_info)}"
                    )
                    print(f"\n🔄 时间有变化！当前可用: {times_str}")
                else:
                    # 没有变化
                    print(f"✅ 仍有空位 ({times_str})，时间无变化，不重复通知")
                
                last_available_times = current_times
            else:
                if last_available_times is not None:
                    # 之前有空位，现在没了
                    send_notification(
                        "😢 MIT网球场空位已满",
                        f"日期: {config.CHECK_DATE}\n之前的可用时间已被预订，继续监控中..."
                    )
                    print("😢 空位已被抢走...")
                    last_available_times = None
                else:
                    print("😔 没有可用时间段")
            
            # 等待下次检查
            wait_time = random.randint(config.CHECK_INTERVAL_MIN, config.CHECK_INTERVAL_MAX)
            print(f"⏳ {wait_time} 秒 ({wait_time // 60}分{wait_time % 60}秒) 后再次检查...")
            time.sleep(wait_time)
            
    except KeyboardInterrupt:
        print("\n\n👋 用户中断，程序退出")
    except Exception as e:
        print(f"❌ 程序出错: {e}")
    finally:
        browser.close()


if __name__ == "__main__":
    run_checker()

