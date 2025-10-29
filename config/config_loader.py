import os
import yaml
from string import Template

def load_config(path: str) -> dict:
    """加载 YAML 并自动替换环境变量"""
    if not os.path.exists(path):
        raise FileNotFoundError(f"配置文件不存在: {path}")

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 替换 ${VAR} 环境变量
    content = Template(content).safe_substitute(os.environ)
    return yaml.safe_load(content)
