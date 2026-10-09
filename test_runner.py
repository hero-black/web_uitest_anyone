"""YAML 测试用例运行器 - 自动收集 testcases/ 下的 YAML 文件并执行"""

import os
import pytest
from engine.yaml_loader import load_test_case
from engine.keyword_engine import KeywordEngine

BASE_DIR = os.path.dirname(__file__)
TESTCASE_DIR = os.path.join(BASE_DIR, 'testcases')


def collect_test_cases():
    """收集 testcases/ 目录下所有 .yaml 用例文件"""
    cases = []
    if os.path.exists(TESTCASE_DIR):
        for f in sorted(os.listdir(TESTCASE_DIR)):
            if f.endswith('.yaml') or f.endswith('.yml'):
                cases.append(os.path.join(TESTCASE_DIR, f))
    return cases


TEST_CASES = collect_test_cases()


@pytest.mark.parametrize(
    'testcase_file', TEST_CASES,
    ids=lambda x: os.path.basename(x).replace('.yaml', '').replace('.yml', '').split('_')[0]
)
def test_run_yaml(testcase_file, playwright_browser, registry, env_config):
    """运行单条 YAML 测试用例

    流程:
      1. 加载 YAML，替换 ${USERNAME}/${PASSWORD} 等变量
      2. 如果用例声明 需要登录: true（默认），先执行登录
      3. 执行步骤 → 断言 → 清理
      4. 检查结果，有失败则 pytest.fail
    """
    # 准备变量
    creds = env_config.get('credentials', {})
    variables = {
        'USERNAME': creds.get('username', ''),
        'PASSWORD': creds.get('password', ''),
    }

    # 加载用例（含变量替换）
    case = load_test_case(testcase_file, variables)

    # 创建引擎
    engine = KeywordEngine(playwright_browser, registry, env_config)

    # 如果需要预先登录
    if case.get('需要登录', True):
        engine._do_登录()

    # 运行用例
    results = engine.run_test_case(case)

    # 打印结果到控制台
    case_name = case.get('用例名称', os.path.basename(testcase_file))
    print(f"\n{'=' * 60}")
    print(f"用例: {case_name}")
    print(f"{'=' * 60}")
    for r in results:
        icon = '✓' if r['status'] == 'pass' else '✗'
        print(f"  {icon} {r['type']}{r['index']}: {r['detail']}")

    # 检查失败
    failures = [r for r in results if r['status'] == 'fail']
    if failures:
        msgs = [f"{r['type']}{r['index']}: {r['detail']}" for r in failures]
        pytest.fail(';\n'.join(msgs))
