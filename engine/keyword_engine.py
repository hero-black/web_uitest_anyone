"""关键字执行引擎 - 解析并执行 YAML 中的操作步骤和断言"""

import os
import time
from playwright.sync_api import expect


class KeywordEngine:
    """解析 YAML 测试用例并逐步执行操作、断言、清理"""

    def __init__(self, page, registry, config):
        self.page = page
        self.registry = registry
        self.config = config
        self.base_url = config.get('base_url', '')
        self.screenshot_dir = os.path.join('reports', 'screenshots')
        os.makedirs(self.screenshot_dir, exist_ok=True)

    # ===== 用例执行入口 =====

    def run_test_case(self, case):
        """运行完整测试用例，返回结果列表

        执行顺序: 步骤 → 断言 → 清理（清理始终执行）
        """
        results = []
        step_failed = False

        # --- 执行步骤 ---
        for i, step in enumerate(case.get('步骤', []), 1):
            try:
                self.execute_step(step)
                results.append({'type': '步骤', 'index': i, 'status': 'pass', 'detail': self._desc(step)})
            except Exception as e:
                self._screenshot(f'step_{i}_fail')
                results.append({'type': '步骤', 'index': i, 'status': 'fail', 'detail': str(e)})
                step_failed = True
                break

        # --- 执行断言（仅当步骤全部通过）---
        if not step_failed:
            for i, assertion in enumerate(case.get('预期', []), 1):
                try:
                    self.execute_assertion(assertion)
                    results.append({'type': '断言', 'index': i, 'status': 'pass', 'detail': self._desc(assertion)})
                except Exception as e:
                    self._screenshot(f'assert_{i}_fail')
                    results.append({'type': '断言', 'index': i, 'status': 'fail', 'detail': str(e)})
                    break

        # --- 执行清理（始终执行，失败不中断）---
        for i, step in enumerate(case.get('清理', []), 1):
            try:
                self.execute_step(step)
                results.append({'type': '清理', 'index': i, 'status': 'pass', 'detail': self._desc(step)})
            except Exception as e:
                results.append({'type': '清理', 'index': i, 'status': 'fail', 'detail': str(e)})

        return results

    # 可在步骤中使用的断言关键字（立即校验，失败即中断）
    ASSERT_KEYWORDS = ('看到文字', '不看到文字', '元素出现', '元素消失', 'URL包含')

    def execute_step(self, step):
        """执行单个操作步骤（步骤中允许穿插断言）"""
        if isinstance(step, dict):
            for action, params in step.items():
                # 断言关键字：立即执行断言
                if action in self.ASSERT_KEYWORDS:
                    self.execute_assertion({action: params})
                    continue
                handler = getattr(self, f'_do_{action}', None)
                if handler is None:
                    raise ValueError(
                        f"不支持的操作 '{action}'。"
                        f"支持: 打开, 点击, 输入, 选择, 下拉选择, 等待, 截图, 刷新, 返回, 登录；"
                        f"步骤内断言: {', '.join(self.ASSERT_KEYWORDS)}"
                    )
                handler(params)
        elif isinstance(step, str):
            handler = getattr(self, f'_do_{step}', None)
            if handler:
                handler(None)
            else:
                raise ValueError(f"不支持的操作 '{step}'")

    def execute_assertion(self, assertion):
        """执行单个断言"""
        if isinstance(assertion, dict):
            for assert_type, value in assertion.items():
                handler = getattr(self, f'_assert_{assert_type}', None)
                if handler is None:
                    raise ValueError(
                        f"不支持的断言 '{assert_type}'。"
                        f"支持: 看到文字, 不看到文字, 元素出现, 元素消失, URL包含"
                    )
                handler(value)

    # ===== 操作关键字 =====

    def _do_打开(self, target):
        """打开页面"""
        if target == '登录页':
            url = self.base_url + self.config.get('login_path', '')
        elif target and str(target).startswith('http'):
            url = str(target)
        else:
            url = self.base_url + str(target or '')
        self.page.goto(url)

    def _do_点击(self, target):
        """点击元素（多个匹配时优先点可见的）"""
        locator = self._get_locator(target)
        # 如果有多个匹配，找第一个可见的点击
        count = locator.count()
        if count > 1:
            for i in range(count):
                item = locator.nth(i)
                if item.is_visible():
                    item.click()
                    return
            # 全部不可见，等待第一个变可见
        locator.wait_for(state='visible', timeout=10000)
        locator.click()

    def _do_输入(self, params):
        """在元素中输入文本"""
        if isinstance(params, dict):
            element_name = params.get('元素') or params.get('element', '')
            content = str(params.get('内容') or params.get('content', ''))
        else:
            raise ValueError("输入操作需要 '元素' 和 '内容'，例如: 输入: {元素: 用户名输入框, 内容: admin}")
        locator = self._get_locator(element_name)
        locator.wait_for(state='visible', timeout=10000)
        locator.fill(content)

    def _do_选择(self, params):
        """选择原生select下拉选项"""
        if isinstance(params, dict):
            element_name = params.get('元素', '')
            value = str(params.get('选项') or params.get('value', ''))
        else:
            raise ValueError("选择操作需要 '元素' 和 '选项'")
        locator = self._get_locator(element_name)
        locator.wait_for(state='visible', timeout=10000)
        locator.select_option(value)

    def _do_下拉选择(self, params):
        """Element UI el-select 下拉选择：点击打开 → 点击选项"""
        if isinstance(params, dict):
            element_name = params.get('元素', '')
            option_text = str(params.get('选项') or params.get('value', ''))
        else:
            raise ValueError("下拉选择需要 '元素' 和 '选项'，例如: 下拉选择: {元素: 协议类型, 选项: http}")

        # 第1步：点击下拉框打开选项面板
        select_locator = self._get_locator(element_name)
        select_locator.wait_for(state='visible', timeout=10000)
        select_locator.click()
        self.page.wait_for_timeout(500)

        # 第2步：在可见的下拉面板中点击选项
        # Element UI 下拉面板 .el-select-dropdown，隐藏的设 display:none
        dropdown = self.page.locator(".el-select-dropdown:not([style*='display: none'])")
        option = dropdown.locator(f".el-select-dropdown__item:has-text('{option_text}')")
        option.click()

    def _do_等待(self, params):
        """等待：元素可见 / 文字出现 / 指定秒数"""
        if isinstance(params, (int, float)):
            self.page.wait_for_timeout(int(params * 1000))
        elif isinstance(params, str):
            self.page.wait_for_selector(f'text={params}', timeout=10000)
        elif isinstance(params, dict):
            if '元素' in params:
                self._get_locator(params['元素']).wait_for(state='visible', timeout=10000)
            elif '文字' in params:
                self.page.wait_for_selector(f"text={params['文字']}", timeout=10000)
            elif '秒' in params:
                self.page.wait_for_timeout(int(float(params['秒']) * 1000))

    def _do_截图(self, name='screenshot'):
        """截图"""
        self._screenshot(name)

    def _do_刷新(self, _=None):
        """刷新页面"""
        self.page.reload()

    def _do_返回(self, _=None):
        """返回上一页"""
        self.page.go_back()

    def _do_登录(self, _=None):
        """执行完整登录流程（使用 env_config 中的账号密码）"""
        self._do_打开('登录页')
        self.page.wait_for_timeout(2000)

        # 检查是否需要登录（如果登录表单不可见，说明已登录）
        try:
            user_input = self._get_locator('用户名输入框')
            if not user_input.is_visible(timeout=3000):
                # 已登录，等待菜单加载
                try:
                    self.page.wait_for_selector('.el-menu', timeout=10000)
                except Exception:
                    pass
                self.page.wait_for_timeout(2000)
                return
        except Exception:
            # 元素未找到，可能已登录
            try:
                self.page.wait_for_selector('.el-menu', timeout=10000)
            except Exception:
                pass
            self.page.wait_for_timeout(2000)
            return

        creds = self.config.get('credentials', {})
        self._do_输入({'元素': '用户名输入框', '内容': creds.get('username', '')})
        self._do_输入({'元素': '密码输入框', '内容': creds.get('password', '')})
        self._do_点击('登录按钮')
        self.page.wait_for_timeout(5000)

    # ===== 断言关键字 =====

    def _assert_看到文字(self, text):
        """断言页面出现指定文字"""
        expect(self.page.locator(f'text={text}')).to_be_visible()

    def _assert_不看到文字(self, text):
        """断言页面不出现指定文字"""
        expect(self.page.locator(f'text={text}')).to_be_hidden()

    def _assert_元素出现(self, element_name):
        """断言元素可见"""
        locator = self._get_locator(element_name)
        expect(locator).to_be_visible()

    def _assert_元素消失(self, element_name):
        """断言元素不可见"""
        locator = self._get_locator(element_name)
        expect(locator).to_be_hidden()

    def _assert_URL包含(self, text):
        """断言当前 URL 包含指定文本"""
        current_url = self.page.url
        assert text in current_url, f"当前 URL '{current_url}' 不包含 '{text}'"

    # ===== 辅助方法 =====

    def _get_locator(self, element_name):
        """根据中文别名获取 Playwright 定位器"""
        loc_method, selector = self.registry.find_element(element_name)

        if loc_method == 'css':
            return self.page.locator(selector).first
        elif loc_method == 'text':
            return self.page.locator(f'text={selector}').first
        elif loc_method == 'placeholder':
            return self.page.locator(f"[placeholder='{selector}']").first
        elif loc_method == 'xpath':
            return self.page.locator(f'xpath={selector}').first
        elif loc_method == 'id':
            return self.page.locator(f'#{selector}').first
        elif loc_method == 'role':
            return self.page.get_by_role(selector).first
        elif loc_method == 'label':
            return self.page.get_by_label(selector).first
        elif loc_method == 'test_id':
            return self.page.get_by_test_id(selector).first
        else:
            return self.page.locator(selector).first

    def _screenshot(self, name):
        """截图并保存到 reports/screenshots/"""
        path = os.path.join(self.screenshot_dir, f'{name}_{int(time.time())}.png')
        self.page.screenshot(path=path)
        return path

    def _desc(self, item):
        """生成可读描述"""
        return str(item)
