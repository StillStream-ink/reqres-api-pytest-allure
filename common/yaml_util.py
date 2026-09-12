import yaml
import re

def read_yaml(file_path):
    """读取yaml文件"""
    with open(file_path, encoding="utf-8") as f:
        return yaml.safe_load(f)

def replace_placeholder(text, data):
    """
    占位符替换：把 {post_id} 替换成实际值
    """
    if not isinstance(text, str):
        return text
    pattern = re.compile(r"\{(\w+)\}")
    def repl(match):
        key = match.group(1)
        if key not in data:
            raise KeyError(f"占位符 {{{key}}} 在数据中不存在，请检查 YAML 配置")
        return str(data[key])
    return pattern.sub(repl, text)
