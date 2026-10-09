"""pytest 全局配置 - 提供浏览器、配置、元素注册表等 fixture"""

import os
import pytest
from playwright.sync_api import sync_playwright
from engine.yaml_loader import load_yaml
from engine.page_registry import PageRegistry

BASE_DIR = os.path.dirname(__file__)
CONFIG_DIR = os.path.join(BASE_DIR, 'config')


@pytest.fixture(scope='session')
def env_config():
    """环境配置：登录地址、账号密码、浏览器设置"""
    return load_yaml(os.path.join(CONFIG_DIR, 'env_config.yaml'))


@pytest.fixture(scope='session')
def page_elements():
    """页面元素别名映射表"""
    return load_yaml(os.path.join(CONFIG_DIR, 'page_elements.yaml'))


@pytest.fixture(scope='session')
def registry(page_elements):
    """页面元素注册表"""
    return PageRegistry(page_elements)


@pytest.fixture(scope='session')
def playwright_browser(env_config):
    """启动浏览器（整个测试会话共享一个实例）

    浏览器配置在 config/env_config.yaml 中:
      browser.headless: false=有头模式(可看到操作) / true=无头模式
      browser.slow_mo: 每步操作间隔毫秒数，方便观察
    """
    browser_config = env_config.get('browser', {})
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=browser_config.get('headless', False),
            slow_mo=browser_config.get('slow_mo', 0),
        )
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()
        page.set_default_timeout(
            env_config.get('timeout', {}).get('element', 10000)
        )
        yield page
        context.close()
        browser.close()
