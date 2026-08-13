import yaml

def read_yaml(file_path):
    """
    读取yaml文件，返回字典
    :param file_path: yaml文件路径
    :return: dict
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data
    except Exception as e:
        raise FileNotFoundError(f"读取yaml失败：{e}")
