"""浏览器模块 - 管理 Playwright 浏览器操作"""

import re
import time
from typing import Tuple, List, Optional

from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
from playwright.sync_api import TimeoutError as PlaywrightTimeout

from .config import config


class TennisBrowser:
    """MIT Recreation 网站浏览器操作类"""
    
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.page_ready: bool = False  # 标记页面是否准备好
    
    def start(self) -> bool:
        """启动浏览器"""
        try:
            self.playwright = sync_playwright().start()
            
            # 使用 Firefox 绕过 Cloudflare 检测
            self.browser = self.playwright.firefox.launch(
                headless=config.HEADLESS,
                args=[]
            )
            
            self.context = self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
                locale="en-US",
                timezone_id="America/New_York"
            )
            
            # 隐藏自动化特征
            self.context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            self.page = self.context.new_page()

            # 拦截非必要资源，减少内存占用
            blocked_extensions = re.compile(
                r"\.(png|jpg|jpeg|gif|svg|webp|ico|woff|woff2|ttf|eot|mp4|mp3|webm|avi)(\?.*)?$",
                re.IGNORECASE
            )
            def _abort_if_media(route):
                if blocked_extensions.search(route.request.url):
                    route.abort()
                else:
                    route.continue_()
            self.page.route("**/*", _abort_if_media)

            print("✅ 浏览器已启动")
            return True
            
        except Exception as e:
            print(f"❌ 启动浏览器失败: {e}")
            return False
    
    def close(self) -> None:
        """关闭浏览器"""
        try:
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            self.browser = None
            self.context = None
            self.page = None
            self.playwright = None
            print("🔒 浏览器已关闭")
        except Exception as e:
            print(f"⚠️ 关闭浏览器时出错: {e}")
    
    def is_alive(self) -> bool:
        """检查浏览器是否还在运行"""
        try:
            if not self.page or not self.browser:
                return False
            # 尝试获取页面标题来测试连接
            self.page.title()
            return True
        except:
            return False
    
    def restart(self) -> bool:
        """重启浏览器并重新登录"""
        print("🔄 正在重启浏览器...")
        self.close()
        time.sleep(2)
        
        if not self.start():
            return False
        
        return self.login()
    
    def login(self) -> bool:
        """登录 MIT Recreation"""
        print("🔐 正在登录 MIT Recreation...")
        
        try:
            self.page.goto(config.RESERVATION_URL, timeout=60000)
            self.page.wait_for_load_state("domcontentloaded", timeout=30000)
            time.sleep(3)
            
            print(f"📍 当前URL: {self.page.url}")
            
            # 检查是否已登录
            if "Welcome," in self.page.content() and "Logout" in self.page.content():
                print("✅ 已经登录!")
                return True
            
            # 查找用户名输入框
            username_input = self._find_element([
                "input[type='text']",
                "input[type='email']",
                "input[name='username']",
                "input[name='email']",
                "#username",
                "#email"
            ])
            
            if not username_input:
                print("⚠️ 找不到用户名输入框，尝试通用 input...")
                self.page.wait_for_selector("input", timeout=30000)
                username_input = self.page.locator("input").first
            
            username_input.fill(config.MIT_USERNAME)
            print("✅ 已填写用户名")
            
            # 填写密码
            password_input = self.page.locator("input[type='password']")
            if password_input.count() > 0:
                password_input.fill(config.MIT_PASSWORD)
                print("✅ 已填写密码")
            else:
                print("❌ 找不到密码输入框")
                return False
            
            # 点击登录按钮
            login_button = self._find_element([
                "button:has-text('Login')",
                "button:has-text('Sign In')",
                "input[type='submit']",
                "button[type='submit']"
            ])
            
            if login_button:
                login_button.click()
            else:
                print("⚠️ 找不到登录按钮，尝试按回车...")
                password_input.press("Enter")
            
            self.page.wait_for_load_state("networkidle", timeout=30000)
            time.sleep(3)
            
            print(f"📍 登录后URL: {self.page.url}")
            
            # 验证登录状态
            content = self.page.content()
            if "Welcome" in content or "Logout" in content:
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
            return False
        except Exception as e:
            print(f"❌ 登录失败: {e}")
            return False
    
    def prepare_search_page(self) -> bool:
        """
        准备搜索页面（加载页面并选择 Tennis）
        
        Returns:
            是否成功
        """
        self.page_ready = False  # 重置状态
        
        try:
            self.page.goto(config.RESERVATION_URL, timeout=60000)
            self.page.wait_for_load_state("networkidle", timeout=30000)
            time.sleep(5)
            
            print(f"📍 预订页面URL: {self.page.url}")
            print(f"📄 页面标题: {self.page.title()}")
            
            # 调试信息
            if config.DEBUG:
                try:
                    body_text = self.page.locator("body").inner_text()[:500]
                    print(f"📝 页面内容预览: {body_text[:200]}...")
                except:
                    pass
            
            # 检查是否需要重新登录
            content = self.page.content()
            if "login" in content.lower() and "password" in content.lower():
                print("⚠️ 检测到登录页面，需要重新登录")
                return False
            
            # 等待页面元素加载
            try:
                self.page.wait_for_selector("#component_chosen, #component, select, form", timeout=20000)
                print("✅ 页面元素已加载")
            except:
                print("⚠️ 页面元素加载超时，继续尝试...")
            
            # 选择 Tennis（只需要选择一次）
            self._select_tennis()
            
            self.page_ready = True  # 页面准备好了
            return True
            
        except Exception as e:
            print(f"❌ 准备页面出错: {e}")
            self.page_ready = False
            return False
    
    def check_availability(self, check_date: str, first_date: bool = True) -> Tuple[bool, List[str]]:
        """
        检查指定日期的网球场空位
        
        Args:
            check_date: 要检查的日期，格式 MM/DD/YYYY
            first_date: 是否是本轮检查的第一个日期（需要重新加载页面）
        
        Returns:
            (是否有空位, 可用时间列表)
        """
        print(f"\n🔍 正在检查 {check_date} 的网球场空位...")
        
        try:
            # 只有第一个日期需要重新加载页面
            if first_date:
                if not self.prepare_search_page():
                    return False, []
            
            # 设置日期
            self._set_date(check_date)
            
            # 点击搜索
            self._click_search()
            
            # 解析可用时间
            return self._parse_available_times()
            
        except Exception as e:
            print(f"❌ 检查出错: {e}")
            return False, []
    
    def _find_element(self, selectors: List[str]):
        """尝试多个选择器查找元素"""
        for selector in selectors:
            try:
                element = self.page.locator(selector).first
                if element.count() > 0 and element.is_visible(timeout=2000):
                    if config.DEBUG:
                        print(f"✅ 找到元素: {selector}")
                    return element
            except:
                continue
        return None
    
    def _select_tennis(self) -> None:
        """选择 Tennis 运动类型"""
        chosen_dropdown = self.page.locator("#component_chosen .chosen-single")
        if chosen_dropdown.count() > 0:
            chosen_dropdown.click()
            time.sleep(1)
            tennis_option = self.page.locator("#component_chosen .chosen-results li:has-text('Tennis')")
            if tennis_option.count() > 0:
                tennis_option.click()
                print("✅ 已选择 Tennis")
                time.sleep(2)
            else:
                print("❌ 找不到 Tennis 选项")
        else:
            print("⚠️ 找不到 Chosen 下拉框，尝试直接设置...")
            try:
                self.page.evaluate("document.querySelector('#component').value = '2'")
                self.page.evaluate("document.querySelector('#component').dispatchEvent(new Event('change'))")
                print("✅ 已通过 JS 选择 Tennis")
            except Exception as e:
                print(f"⚠️ 设置 Tennis 失败: {e}")
            time.sleep(2)
    
    def _set_date(self, check_date: str) -> None:
        """设置检查日期"""
        date_input = self._find_element([
            "#date",
            "input[name='date']",
            "input.datepicker"
        ])
        
        if date_input:
            try:
                date_input.click()
                time.sleep(0.5)
                date_input.fill("")
                date_input.fill(check_date)
                date_input.press("Escape")
                print(f"✅ 设置日期为: {check_date}")
            except Exception as e:
                print(f"⚠️ 设置日期失败: {e}")
            time.sleep(1)
        else:
            print("❌ 找不到日期输入框")
        
        # 关闭可能的弹窗
        self.page.locator("body").click(position={"x": 10, "y": 10})
        time.sleep(0.5)
    
    def _click_search(self) -> None:
        """点击搜索按钮"""
        search_button = self._find_element([
            "button:has-text('Search')",
            "input[value='Search']",
            ".search-button",
            "#search"
        ])
        
        if search_button:
            print("✅ 点击搜索按钮...")
            search_button.click()
            self.page.wait_for_load_state("networkidle")
            time.sleep(3)
        else:
            print("❌ 找不到搜索按钮")
    
    def _parse_available_times(self) -> Tuple[bool, List[str]]:
        """解析可用时间"""
        page_content = self.page.content()
        
        # 检查是否明确显示没有空位
        if "No available times" in page_content or "no availability" in page_content.lower():
            return False, []
        
        # 查找时间链接
        time_pattern = re.compile(r'\d{1,2}:\d{2}\s*(am|pm)', re.IGNORECASE)
        time_links = self.page.locator(".td-blue a, a[href='javascript:void(0);']").all()
        
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

