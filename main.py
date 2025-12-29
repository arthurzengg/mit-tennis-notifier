#!/usr/bin/env python3
"""
MIT Tennis Court Availability Checker
主入口点 - 支持同时检测多个日期
"""

import time
import random
from datetime import datetime
from typing import Dict, List, Optional

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
        consecutive_errors = 0
        max_consecutive_errors = 3
        
        # 每个日期的上次可用时间记录
        # 格式: {"12/27/2025": ["10:00 am", "2:00 pm"], ...}
        last_available_times: Dict[str, Optional[List[str]]] = {
            date: None for date in config.CHECK_DATES
        }
        
        # 主循环
        while True:
            check_count += 1
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n{'=' * 60}")
            print(f"[{current_time}] 第 {check_count} 次检查 ({len(config.CHECK_DATES)} 个日期)")
            print(f"{'=' * 60}")
            
            # 检查浏览器是否还活着
            if not browser.is_alive():
                print("⚠️ 检测到浏览器已关闭，正在重启...")
                if not browser.restart():
                    print("❌ 重启浏览器失败，等待后重试...")
                    time.sleep(30)
                    continue
                consecutive_errors = 0
            
            # 遍历每个日期进行检查
            has_error = False
            for check_date in config.CHECK_DATES:
                available, current_times = browser.check_availability(check_date)
                
                # 检查是否有错误
                if not available and not current_times:
                    if not browser.is_alive():
                        has_error = True
                        break  # 浏览器崩溃，跳出循环
                
                # 获取该日期上次的可用时间
                last_times = last_available_times.get(check_date)
                
                if available:
                    times_str = ", ".join(current_times)
                    
                    if last_times is None:
                        # 首次检测到空位
                        send_notification(
                            "🎾 MIT网球场有空位!",
                            f"日期: {check_date}\n可用时间: {times_str}\n快去预订!"
                        )
                        print(f"\n🎉 [{check_date}] 检测到空位！")
                        
                    elif set(current_times) != set(last_times):
                        # 可用时间有变化
                        new_times = set(current_times) - set(last_times)
                        removed_times = set(last_times) - set(current_times)
                        
                        change_info = []
                        if new_times:
                            change_info.append(f"🆕 新增: {', '.join(sorted(new_times))}")
                        if removed_times:
                            change_info.append(f"❌ 已无: {', '.join(sorted(removed_times))}")
                        
                        send_notification(
                            "🔄 MIT网球场时间更新!",
                            f"日期: {check_date}\n当前可用: {times_str}\n{chr(10).join(change_info)}"
                        )
                        print(f"\n🔄 [{check_date}] 时间有变化！当前可用: {times_str}")
                    else:
                        # 没有变化
                        print(f"✅ [{check_date}] 仍有空位 ({times_str})，无变化")
                    
                    last_available_times[check_date] = current_times
                else:
                    if last_times is not None:
                        # 之前有空位，现在没了
                        send_notification(
                            "😢 MIT网球场空位已满",
                            f"日期: {check_date}\n之前的可用时间已被预订，继续监控中..."
                        )
                        print(f"😢 [{check_date}] 空位已被抢走...")
                        last_available_times[check_date] = None
                    else:
                        print(f"😔 [{check_date}] 没有可用时间段")
                
                # 日期之间稍作间隔，避免请求过快
                if check_date != config.CHECK_DATES[-1]:
                    time.sleep(2)
            
            # 处理错误
            if has_error:
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
                consecutive_errors = 0
            
            # 等待下次检查
            wait_time = random.randint(config.CHECK_INTERVAL_MIN, config.CHECK_INTERVAL_MAX)
            print(f"\n⏳ {wait_time} 秒 ({wait_time // 60}分{wait_time % 60}秒) 后再次检查所有日期...")
            time.sleep(wait_time)
            
    except KeyboardInterrupt:
        print("\n\n👋 用户中断，程序退出")
    except Exception as e:
        print(f"❌ 程序出错: {e}")
    finally:
        browser.close()


if __name__ == "__main__":
    run_checker()
