#!/usr/bin/env python3
"""
MIT Tennis Court Availability Checker
使用 Playwright 自动检测MIT网球场空位并通知
"""

import os
import sys
import time
import random
import platform
import subprocess
import urllib.request
import urllib.parse
from datetime import datetime
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# 确保输出不被缓冲（Docker 容器中重要）
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

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
    
    try:
        page.goto(RESERVATION_URL, timeout=60000)
        
        # 等待页面加载
        page.wait_for_load_state("domcontentloaded", timeout=30000)
        time.sleep(3)  # 额外等待 JS 加载
        
        print(f"📍 当前URL: {page.url}")
        
        # 检查是否已经登录
        if "Welcome," in page.content() and "Logout" in page.content():
            print("✅ 已经登录!")
            return True
        
        # 尝试多种选择器找到登录表单
        selectors_to_try = [
            "input[type='text']",
            "input[type='email']",
            "input[name='username']",
            "input[name='email']",
            "#username",
            "#email",
            "input:not([type='hidden']):not([type='password'])"
        ]
        
        username_input = None
        for selector in selectors_to_try:
            try:
                element = page.locator(selector).first
                if element.count() > 0 and element.is_visible(timeout=2000):
                    username_input = element
                    print(f"✅ 找到用户名输入框: {selector}")
                    break
            except:
                continue
        
        if not username_input:
            print("⚠️ 找不到用户名输入框，尝试通用 input...")
            page.wait_for_selector("input", timeout=30000)
            username_input = page.locator("input").first
        
        # 填写用户名
        username_input.fill(MIT_USERNAME)
        print("✅ 已填写用户名")
        
        # 查找并填写密码
        password_input = page.locator("input[type='password']")
        if password_input.count() > 0:
            password_input.fill(MIT_PASSWORD)
            print("✅ 已填写密码")
        else:
            print("❌ 找不到密码输入框")
            return False
        
        # 查找并点击登录按钮
        button_selectors = [
            "button:has-text('Login')",
            "button:has-text('Sign In')",
            "input[type='submit']",
            "button[type='submit']",
            ".login-button",
            "#login-button"
        ]
        
        login_button = None
        for selector in button_selectors:
            try:
                element = page.locator(selector)
                if element.count() > 0:
                    login_button = element.first
                    print(f"✅ 找到登录按钮: {selector}")
                    break
            except:
                continue
        
        if login_button:
            login_button.click()
        else:
            print("⚠️ 找不到登录按钮，尝试按回车...")
            password_input.press("Enter")
        
        # 等待登录完成
        page.wait_for_load_state("networkidle", timeout=30000)
        time.sleep(3)
        
        print(f"📍 登录后URL: {page.url}")
        
        # 验证登录状态
        content = page.content()
        if "Welcome" in content or "Logout" in content or "logout" in content.lower():
            print("✅ 登录成功!")
            return True
        elif "invalid" in content.lower() or "incorrect" in content.lower():
            print("❌ 用户名或密码错误")
            return False
        else:
            print("⚠️ 登录状态不确定，继续尝试...")
            return True
            
    except PlaywrightTimeout as e:
        print(f"❌ 超时: {e}")
        # 打印页面标题帮助调试
        try:
            print(f"📄 页面标题: {page.title()}")
        except:
            pass
        return False
    except Exception as e:
        print(f"❌ 登录失败: {e}")
        return False


def check_availability(page):
    """检查网球场空位"""
    print(f"\n🔍 正在检查 {CHECK_DATE} 的网球场空位...")
    
    try:
        # 导航到预订页面
        page.goto(RESERVATION_URL, timeout=60000)
        page.wait_for_load_state("networkidle", timeout=30000)
        time.sleep(5)  # 云端需要更多时间
        
        print(f"📍 预订页面URL: {page.url}")
        print(f"📄 页面标题: {page.title()}")
        
        # 调试：打印页面部分内容
        try:
            body_text = page.locator("body").inner_text()[:500]
            print(f"📝 页面内容预览: {body_text[:200]}...")
        except Exception as e:
            print(f"⚠️ 无法获取页面内容: {e}")
        
        # 检查是否有错误或需要重新登录
        content = page.content()
        if "login" in content.lower() and "password" in content.lower():
            print("⚠️ 检测到登录页面，可能需要重新登录")
            return False, []
        
        # 等待页面核心元素加载
        try:
            page.wait_for_selector("#component_chosen, #component, select, form", timeout=20000)
            print("✅ 页面元素已加载")
        except:
            print("⚠️ 页面元素加载超时，继续尝试...")
            # 打印所有表单元素帮助调试
            forms = page.locator("form").count()
            inputs = page.locator("input").count()
            selects = page.locator("select").count()
            print(f"📊 页面元素: {forms} 个表单, {inputs} 个输入框, {selects} 个下拉框")
        
        # 选择 Tennis (Chosen 自定义下拉框)
        # 先点击展开下拉框
        chosen_dropdown = page.locator("#component_chosen .chosen-single")
        if chosen_dropdown.count() > 0:
            chosen_dropdown.click()
            time.sleep(1)
            # 点击 Tennis 选项
            tennis_option = page.locator("#component_chosen .chosen-results li:has-text('Tennis')")
            if tennis_option.count() > 0:
                tennis_option.click()
                print("✅ 已选择 Tennis")
                time.sleep(2)
            else:
                print("❌ 找不到 Tennis 选项")
        else:
            # 备用方案：直接操作隐藏的 select
            print("⚠️ 找不到 Chosen 下拉框，尝试直接设置...")
            try:
                page.evaluate("document.querySelector('#component').value = '2'")
                page.evaluate("document.querySelector('#component').dispatchEvent(new Event('change'))")
                print("✅ 已通过 JS 选择 Tennis")
            except Exception as e:
                print(f"⚠️ 设置 Tennis 失败: {e}")
            time.sleep(2)
        
        # 等待日期输入框出现
        date_selectors = ["#date", "input[name='date']", "input.datepicker", "input[type='text'][placeholder*='date']"]
        date_input = None
        
        for selector in date_selectors:
            try:
                element = page.locator(selector)
                if element.count() > 0 and element.first.is_visible(timeout=3000):
                    date_input = element.first
                    print(f"✅ 找到日期输入框: {selector}")
                    break
            except:
                continue
        
        if date_input:
            # 使用 Playwright 原生方法设置日期（更可靠）
            try:
                date_input.click()
                time.sleep(0.5)
                date_input.fill("")  # 先清空
                date_input.fill(CHECK_DATE)
                date_input.press("Escape")  # 关闭可能的日历弹窗
                print(f"✅ 设置日期为: {CHECK_DATE}")
            except Exception as e:
                print(f"⚠️ Playwright 设置日期失败，尝试 JS: {e}")
                # 备用：JavaScript 方式
                page.evaluate(f"""
                    var inputs = document.querySelectorAll('input');
                    for (var i = 0; i < inputs.length; i++) {{
                        if (inputs[i].id === 'date' || inputs[i].name === 'date') {{
                            inputs[i].value = '{CHECK_DATE}';
                            inputs[i].dispatchEvent(new Event('change', {{ bubbles: true }}));
                            break;
                        }}
                    }}
                """)
            time.sleep(1)
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
    print("="*60, flush=True)
    print("🎾 MIT Tennis Court Availability Checker", flush=True)
    print(f"📅 检测日期: {CHECK_DATE}", flush=True)
    print(f"⏱️  检测间隔: {CHECK_INTERVAL_MIN//60}-{CHECK_INTERVAL_MAX//60} 分钟随机", flush=True)
    print(f"🖥️  Headless 模式: {HEADLESS}", flush=True)
    print("="*60, flush=True)
    
    # 检查环境变量
    print(f"🔍 MIT_USERNAME: {'已设置' if MIT_USERNAME else '❌ 未设置'}", flush=True)
    print(f"🔍 MIT_PASSWORD: {'已设置' if MIT_PASSWORD else '❌ 未设置'}", flush=True)
    
    if not MIT_USERNAME or not MIT_PASSWORD:
        print("❌ 错误: 请在环境变量中设置 MIT_USERNAME 和 MIT_PASSWORD", flush=True)
        print("   Railway: Settings -> Variables", flush=True)
        # 等待一会再退出，确保日志被写入
        time.sleep(5)
        return
    
    with sync_playwright() as p:
        # 启动浏览器（云端部署时使用 headless 模式）
        # 使用 Firefox 可以更好地绕过 Cloudflare 检测
        browser = p.firefox.launch(
            headless=HEADLESS,
            args=[]
        )
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            locale="en-US",
            timezone_id="America/New_York"
        )
        
        # 添加初始化脚本来隐藏自动化特征
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
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
                
                wait_time = random.randint(CHECK_INTERVAL_MIN, CHECK_INTERVAL_MAX)
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
