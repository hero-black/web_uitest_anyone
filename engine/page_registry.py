"""页面元素注册表 - 管理中文别名到定位器的映射"""


class PageRegistry:
    """根据中文别名查找元素的定位方式（CSS/XPath/Text 等）"""

    def __init__(self, elements_config):
        self.elements = elements_config or {}

    def find_element(self, element_name):
        """根据中文别名查找元素定位信息

        返回: (定位方式, 选择器)
        例如: ('css', 'input[placeholder="请输入用户名"]')
        """
        for page_name, page_elements in self.elements.items():
            if isinstance(page_elements, dict) and element_name in page_elements:
                el = page_elements[element_name]
                return el.get('定位方式', 'css'), el.get('选择器', '')
        raise KeyError(
            f"元素 '{element_name}' 未在 page_elements.yaml 中注册。"
            f"请在 config/page_elements.yaml 中添加该元素的定位信息。"
        )

    def list_all_elements(self):
        """列出所有已注册元素，返回 {元素名: 所在页面名}"""
        result = {}
        for page_name, page_elements in self.elements.items():
            if isinstance(page_elements, dict):
                for el_name in page_elements:
                    result[el_name] = page_name
        return result
