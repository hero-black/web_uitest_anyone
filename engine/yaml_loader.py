"""YAML 文件加载与变量替换"""

import yaml


def load_yaml(file_path):
    """加载 YAML 文件，返回字典或列表"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def _replace_variables(obj, variables):
    """递归替换 ${VAR} 变量为实际值"""
    if isinstance(obj, str):
        for key, value in variables.items():
            obj = obj.replace(f'${{{key}}}', str(value))
        return obj
    elif isinstance(obj, dict):
        return {k: _replace_variables(v, variables) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_replace_variables(item, variables) for item in obj]
    return obj


def load_test_case(file_path, variables=None):
    """加载测试用例 YAML，支持 ${VAR} 变量替换

    用例中可使用 ${USERNAME}、${PASSWORD} 等变量，
    传入 variables 字典即可自动替换。
    """
    data = load_yaml(file_path)
    if variables:
        data = _replace_variables(data, variables)
    return data
