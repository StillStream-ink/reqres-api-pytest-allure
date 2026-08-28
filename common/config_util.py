"""
配置读取工具
支持多环境切换、接口定义读取
"""
import os
from common.yaml_util import read_yaml

# 项目根目录
BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_env_config(env_name=None):
    """
    读取当前环境配置
    :param env_name: 环境名，不传则从环境变量 API_ENV 读取，默认 dev
    :return: dict 包含 base_url, timeout, db_name, env_name
    """
    env_file = os.path.join(BASE_PATH, "config", "env_config.yaml")
    config = read_yaml(env_file)
    env = env_name or os.environ.get("API_ENV", config.get("current", "dev"))
    env_config = config["environments"].get(env, config["environments"]["dev"])
    env_config["env_name"] = env
    return env_config


def get_api_data(api_name):
    """
    读取接口定义数据
    :param api_name: 接口名，如 "posts_list", "posts_create"
    :return: dict 包含 url, method, json, expect_code
    """
    api_file = os.path.join(BASE_PATH, "config", "api_data.yaml")
    return read_yaml(api_file).get(api_name)


def build_url(api_name, env_config=None, **path_params):
    """
    构建完整请求 URL
    :param api_name: 接口名
    :param env_config: 环境配置，不传则自动读取
    :param path_params: URL 路径参数，如 post_id=1
    :return: 完整 URL
    """
    cfg = env_config or get_env_config()
    api = get_api_data(api_name)
    if not api:
        raise ValueError(f"接口 {api_name} 未在 api_data.yaml 中定义")

    url = api["url"].format(**path_params)
    return f"{cfg['base_url']}{url}"


# 全局环境配置（启动时加载一次）
ENV_CONFIG = get_env_config()