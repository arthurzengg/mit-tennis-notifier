#!/usr/bin/env python3
"""
MIT Tennis Court Availability Checker
使用 Playwright 自动检测MIT网球场空位并通知
"""

import os
import time
import random
import platform
import subprocess
import urllib.request
import urllib.parse
from datetime import datetime
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# 加载环境变量
load_dotenv()

# 配置
MIT_USERNAME = os.getenv("MIT_USERNAME")
MIT_PASSWORD = os.getenv("MIT_PASSWORD")
CHECK_DATE = os.getenv("CHECK_DATE", "12/22/2025")
# 搜索间隔：2-4分钟随机
CHECK_INTERVAL_MIN = 120  # 2分钟
CHECK_INTERVAL_MAX = 240  # 4分钟

# Telegram 配置 (可选)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 云端部署配置
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"

RESERVATION_URL = "https://mit.clubautomation.com/event/reserve-court-new"


def send_telegram(message: str):
    """发送 Telegram 消息"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = urllib.parse.urlencode({
            "chat_id": TELEGRAM_CHAT_ID,
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


def send_notification(title: str, message: str):
    """发送桌面通知 + 手机通知"""
    system = platform.system()
    
    # 桌面通知
    if system == "Darwin":  # macOS
        script = f'display notification "{message}" with title "{title}" sound name "Glass"'
        subprocess.run(["osascript", "-e", script])
        subprocess.run(["say", f"Good news! Tennis court available on {CHECK_DATE}"])
    elif system == "Linux":
        subprocess.run(["notify-send", title, message])
    elif system == "Windows":
        try:
            from plyer import notification
            notification.notify(title=title, message=message, timeout=10)
        except ImportError:
            pass
    
    # Telegram 手机通知
    telegram_msg = f"🎾 <b>{title}</b>\n\n{message}\n\n🔗 <a href='{RESERVATION_URL}'>立即预订</a>"
    send_telegram(telegram_msg)
    
    print(f"\n{'='*60}")
    print(f"🎾 {title}")
    print(f"📅 {message}")
    print(f"{'='*60}\n")


def login(page):
    """登录MIT Recreation"""
    print(f"🔐 正在登录 MIT Recreation...")
    page.goto(RESERVATION_URL)
    
    # 等待页面加载
    page.wait_for_load_state("networkidle")
    
    # 检查是否已经登录
    if "Welcome," in page.content() and "Logout" in page.content():
        print("✅ 已经登录!")
        return True
    
    print(f"📍 当前URL: {page.url}")
    
    try:
        # 等待登录表单出现
        page.wait_for_selector("input", timeout=10000)
        
        # 查找并填写用户名
        username_input = page.locator("input").first
        if username_input:
            print("✅ 找到用户名输入框")
            username_input.fill(MIT_USERNAME)
        
        # 查找并填写密码
        password_input = page.locator("input[type='password']")
        if password_input.count() > 0:
            print("✅ 找到密码输入框")
            password_input.fill(MIT_PASSWORD)
        
        # 查找并点击登录按钮
        login_button = page.locator("button:has-text('Login')")
        if login_button.count() == 0:
            login_button = page.locator("button[type='submit']")
        if login_button.count() == 0:
            login_button = page.locator("button").first
        
        if login_button.count() > 0:
            print("✅ 找到登录按钮，点击中...")
            login_button.click()
        else:
            # 按回车提交
            print("⚠️ 找不到登录按钮，尝试按回车...")
            password_input.press("Enter")
        
        # 等待登录完成
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        
        # 验证登录状态
        if "Welcome" in page.content() or "Logout" in page.content():
            print("✅ 登录成功!")
            return True
        else:
            print("⚠️ 登录状态不确定，继续尝试...")
            return True
            
    except PlaywrightTimeout as e:
        print(f"❌ 超时: {e}")
        return False
    except Exception as e:
        print(f"❌ 登录失败: {e}")
        return False


def check_availability(page):
    """检查网球场空位"""
    print(f"\n🔍 正在检查 {CHECK_DATE} 的网球场空位...")
    
    try:
        # 导航到预订页面
        page.goto(RESERVATION_URL)
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        
        # 选择 Tennis (Chosen 自定义下拉框)
        # 先点击展开下拉框
        chosen_dropdown = page.locator("#component_chosen .chosen-single")
        if chosen_dropdown.count() > 0:
            chosen_dropdown.click()
            time.sleep(0.5)
            # 点击 Tennis 选项
            tennis_option = page.locator("#component_chosen .chosen-results li:has-text('Tennis')")
            if tennis_option.count() > 0:
                tennis_option.click()
                print("✅ 已选择 Tennis")
                time.sleep(1)
            else:
                print("❌ 找不到 Tennis 选项")
        else:
            # 备用方案：直接操作隐藏的 select
            page.evaluate("document.querySelector('#component').value = '2'")
            page.evaluate("document.querySelector('#component').dispatchEvent(new Event('change'))")
            print("✅ 已通过 JS 选择 Tennis")
            time.sleep(1)
        
        # 设置日期 (使用 JavaScript 直接设置，避免日历弹窗问题)
        date_input = page.locator("#date, input[name='date']").first
        if date_input.count() > 0:
            # 使用 JavaScript 直接设置日期值，不触发日历
            page.evaluate(f"""
                var dateInput = document.querySelector('#date') || document.querySelector('input[name="date"]');
                if (dateInput) {{
                    dateInput.value = '{CHECK_DATE}';
                    dateInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                }}
            """)
            print(f"✅ 设置日期为: {CHECK_DATE}")
            time.sleep(0.5)
        else:
            print("❌ 找不到日期输入框")
        
        # 点击页面空白处确保任何弹窗关闭
        page.locator("body").click(position={"x": 10, "y": 10})
        time.sleep(0.5)
        
        # 点击搜索按钮
        search_button = page.locator("button:has-text('Search')")
        if search_button.count() == 0:
            search_button = page.locator("input[value='Search']")
        if search_button.count() == 0:
            search_button = page.locator(".search-button, #search")
        
        if search_button.count() > 0:
            print("✅ 点击搜索按钮...")
            search_button.click()
            page.wait_for_load_state("networkidle")
            time.sleep(3)
        else:
            print("❌ 找不到搜索按钮")
        
        # 检查可用时间
        page_content = page.content()
        
        # 首先检查是否明确显示没有空位
        if "No available times" in page_content or "no availability" in page_content.lower():
            return False, "没有可用时间"
        
        # 查找 td-blue 区域下的时间链接
        import re
        time_pattern = re.compile(r'\d{1,2}:\d{2}\s*(am|pm)', re.IGNORECASE)
        
        # 查找所有 .td-blue 下的链接，或者所有 href="javascript:void(0);" 的链接
        time_links = page.locator(".td-blue a, a[href='javascript:void(0);']").all()
        
        available_times = []
        for link in time_links:
            try:
                text = link.inner_text().strip()
                if text and time_pattern.search(text):
                    available_times.append(text)
            except:
                pass
        
        # 去重并排序
        available_times = sorted(set(available_times))
        
        if available_times:
            return True, available_times
        
        return False, []
            
    except Exception as e:
        print(f"❌ 检查出错: {e}")
        return False, []


def main():
    """主函数"""
    print("="*60)
    print("🎾 MIT Tennis Court Availability Checker")
    print(f"📅 检测日期: {CHECK_DATE}")
    print(f"⏱️  检测间隔: {CHECK_INTERVAL_MIN//60}-{CHECK_INTERVAL_MAX//60} 分钟随机")
    print("="*60)
    
    if not MIT_USERNAME or not MIT_PASSWORD:
        print("❌ 错误: 请在 .env 文件中设置 MIT_USERNAME 和 MIT_PASSWORD")
        print("   可以参考 config_example.txt 文件")
        return
    
    with sync_playwright() as p:
        # 启动浏览器（云端部署时使用 headless 模式）
        browser = p.chromium.launch(headless=HEADLESS)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        
        try:
            # 登录
            if not login(page):
                print("❌ 登录失败，退出程序")
                return
            
            check_count = 0
            last_available_times = None  # 记录上次检测到的可用时间
            
            while True:
                check_count += 1
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"\n[{current_time}] 第 {check_count} 次检查...")
                
                available, current_times = check_availability(page)
                
                if available:
                    times_str = ", ".join(current_times)
                    
                    # 检查是否有变化
                    if last_available_times is None:
                        # 首次检测到空位，发送通知
                        send_notification(
                            "🎾 MIT网球场有空位!",
                            f"日期: {CHECK_DATE}\n可用时间: {times_str}\n快去预订!"
                        )
                        print("\n🎉 检测到空位！程序将继续运行以持续监控...")
                    elif set(current_times) != set(last_available_times):
                        # 可用时间有变化，发送更新通知
                        # 计算新增和减少的时间
                        new_times = set(current_times) - set(last_available_times)
                        removed_times = set(last_available_times) - set(current_times)
                        
                        change_info = []
                        if new_times:
                            change_info.append(f"🆕 新增: {', '.join(sorted(new_times))}")
                        if removed_times:
                            change_info.append(f"❌ 已无: {', '.join(sorted(removed_times))}")
                        
                        send_notification(
                            "🔄 MIT网球场时间更新!",
                            f"日期: {CHECK_DATE}\n当前可用: {times_str}\n{chr(10).join(change_info)}"
                        )
                        print(f"\n🔄 时间有变化！当前可用: {times_str}")
                    else:
                        # 没有变化，不发送通知
                        print(f"✅ 仍有空位 ({times_str})，时间无变化，不重复通知")
                    
                    last_available_times = current_times
                else:
                    if last_available_times is not None:
                        # 之前有空位，现在没了，发送通知
                        send_notification(
                            "😢 MIT网球场空位已满",
                            f"日期: {CHECK_DATE}\n之前的可用时间已被预订，继续监控中..."
                        )
                        print("😢 空位已被抢走...")
                        last_available_times = None
                    else:
                        print("😔 没有可用时间段")
                
                wait_time = 10
                print(f"⏳ {wait_time} 秒 ({wait_time//60}分{wait_time%60}秒) 后再次检查...")
                time.sleep(wait_time)
                
        except KeyboardInterrupt:
            print("\n\n👋 用户中断，程序退出")
        except Exception as e:
            print(f"❌ 程序出错: {e}")
        finally:
            browser.close()
            print("🔒 浏览器已关闭")


if __name__ == "__main__":
    main()
