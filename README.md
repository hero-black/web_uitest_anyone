# Web 自动化测试框架

基于 Playwright + pytest 的关键字驱动 Web 自动化测试框架。
业务人员用 YAML 编写测试用例（中文关键字），无需写代码。

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. 配置环境

编辑 `config/env_config.yaml`，修改登录地址和账号密码：

```yaml
base_url: "http://192.168.12.225:8080"
login_path: "/html/login/index.html#/login"
credentials:
  username: "你的用户名"
  password: "你的密码"
```

### 3. 运行测试

```bash
pytest
```

浏览器会自动打开，按用例步骤操作，结束后在 `reports/` 查看报告。

---

## 目录结构

```
项目根目录/
├── config/                  # 配置目录
│   ├── env_config.yaml     # 环境配置（地址、账号、浏览器）
│   └── page_elements.yaml  # 页面元素别名映射（核心）
├── testcases/               # 测试用例目录（YAML）
│   ├── 01_登录成功.yaml
│   ├── 02_新建数据源.yaml
│   └── 03_新建任务.yaml
├── engine/                  # 测试引擎（无需修改）
│   ├── yaml_loader.py       # YAML解析器
│   ├── page_registry.py     # 元素注册表
│   └── keyword_engine.py    # 关键字执行引擎
├── conftest.py              # pytest全局配置（无需修改）
├── test_runner.py           # 测试运行器（无需修改）
├── requirements.txt         # Python依赖
└── reports/                 # 测试报告输出
```

---

## 如何编写测试用例

在 `testcases/` 目录下创建 `.yaml` 文件，格式如下：

```yaml
用例名称: 新建商品成功      # 必填，用例标题
描述: 登录后新建商品并验证   # 选填
需要登录: true              # 是否需要预先登录（默认true）

步骤:                        # 操作步骤
  - 点击: 商品管理菜单
  - 点击: 新建按钮
  - 输入: {元素: 商品名称输入框, 内容: "测试商品"}
  - 点击: 保存按钮
  - 等待: 2

预期:                        # 预期结果（断言）
  - 看到文字: 保存成功

清理:                        # 清理步骤（始终执行，即使前面失败）
  - 点击: 删除按钮
```

### 支持的操作关键字

| 关键字 | 格式 | 说明 |
|--------|------|------|
| 打开 | `打开: 登录页` 或 `打开: /path` | 打开页面 |
| 点击 | `点击: 按钮别名` | 点击元素 |
| 输入 | `输入: {元素: 输入框别名, 内容: "文本"}` | 输入文本 |
| 选择 | `选择: {元素: 下拉框别名, 选项: "值"}` | 选择下拉选项 |
| 等待 | `等待: 2` 或 `等待: {元素: 加载框}` | 等待时间/元素/文字 |
| 截图 | `截图: 名称` | 截图保存到 reports/screenshots/ |
| 刷新 | `刷新:` | 刷新页面 |
| 返回 | `返回:` | 返回上一页 |
| 登录 | `登录:` | 执行完整登录流程 |

### 支持的断言关键字

| 关键字 | 格式 | 说明 |
|--------|------|------|
| 看到文字 | `看到文字: 保存成功` | 断言页面出现该文字 |
| 不看到文字 | `不看到文字: 登录` | 断言页面不出现该文字 |
| 元素出现 | `元素出现: 元素别名` | 断言元素可见 |
| 元素消失 | `元素消失: 元素别名` | 断言元素不可见 |
| URL包含 | `URL包含: index` | 断言URL包含指定文本 |

### 变量替换

用例中可使用 `${USERNAME}` 和 `${PASSWORD}`，运行时自动替换为 `env_config.yaml` 中配置的值。

---

## 如何添加页面元素

编辑 `config/page_elements.yaml`，为页面元素注册中文别名：

```yaml
登录页:
  用户名输入框:
    定位方式: placeholder
    选择器: "请输入用户名"
  密码输入框:
    定位方式: placeholder
    选择器: "请输入密码"
  登录按钮:
    定位方式: text
    选择器: "登录"
```

### 定位方式说明

| 定位方式 | 选择器格式 | 适用场景 |
|---------|----------|---------|
| css | `"input.username"` | CSS选择器（最常用） |
| text | `"登录"` | 按文本内容定位按钮/链接 |
| placeholder | `"请输入用户名"` | 按输入框placeholder定位 |
| id | `"login-btn"` | 按元素ID定位 |
| xpath | `"//div[@class='login']"` | XPath定位 |

### 如何查找元素选择器

1. 在 Chrome 中打开被测页面
2. 按 `F12` 打开开发者工具
3. 点击左上角的元素选择器箭头
4. 点击要定位的页面元素
5. 在 Elements 面板中右键元素 → Copy → Copy selector
6. 粘贴到 `page_elements.yaml` 的选择器字段

---

## 运行指定用例

```bash
# 运行所有用例
pytest

# 运行指定用例（用 -k 按编号过滤）
pytest -k 01              # 运行 01_登录成功
pytest -k 02              # 运行 02_新建数据源
pytest -k 03              # 运行 03_新建任务

# 无头模式（后台运行，不弹浏览器）
# 在 env_config.yaml 中设置 browser.headless: true
```

## 查看报告

测试完成后，打开 `reports/report.html` 查看详细报告。
失败步骤的截图保存在 `reports/screenshots/` 目录。
