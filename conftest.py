import pytest
import threading
import time
import sys
import os
import json

# 确保项目根目录在 Python 路径里（防止 import 找不到）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common.yaml_util import read_yaml
from common.log_util import logger
from common.mock_server import app, init_db

# 全局存储公共请求头
global_headers = {}

# ---------------------- 自动启动本地 Mock 服务 ----------------------
@pytest.fixture(scope="session", autouse=True)
def live_server():
    """测试会话开始前启动 Flask，结束后自动关闭并清理数据库"""
    init_db()  # 重置数据库，保证环境干净
    server = threading.Thread(target=app.run, kwargs={
        'host': '127.0.0.1',
        'port': 5000,
        'debug': False,
        'use_reloader': False     # 必须关！Flask 热重载会和 pytest 多线程冲突
    })
    server.daemon = True
    server.start()
    time.sleep(1.5)  # 等待服务启动
    yield
    # 测试结束后清理数据库文件
    db_path = os.path.join(os.path.dirname(__file__), 'test_mock.db')
    if os.path.exists(db_path):
        os.remove(db_path)

# ---------------------- Allure报告全局钩子 ----------------------
@pytest.fixture(autouse=True)
def allure_env_info():
    """自动写入Allure环境信息 + 执行者信息"""
    env_content = """Project=ReqRes接口自动化测试
BaseUrl=http://127.0.0.1:5000
System=Windows10
Python=3.11.5
Framework=pytest
Env=local_mock
"""
    result_path = "allure-results/environment.properties"
    if not os.path.exists("allure-results"):
        os.makedirs("allure-results")
    with open(result_path, "w", encoding="utf-8") as f:
        f.write(env_content)

    # 执行者信息
    executor = {
        "name": "Jenkins",
        "type": "jenkins",
        "buildName": "Local-Dev"
    }
    with open("allure-results/executor.json", "w", encoding="utf-8") as f:
        json.dump(executor, f, ensure_ascii=False, indent=2)

# ---------------------- pytest全局钩子 ----------------------
def pytest_runtest_setup(item):
    """每个用例执行前触发"""
    logger.info(f"\n========== 开始执行用例：{item.nodeid} ==========")

def pytest_runtest_teardown(item):
    """每个用例执行完成后触发"""
    logger.info(f"========== 用例执行结束：{item.nodeid} ==========\n")

def pytest_runtest_makereport(item, call):
    """捕获用例失败，自动记录日志"""
    if call.when == "call" and call.excinfo is not None:
        logger.error(f"❌ 用例失败：{item.nodeid}，错误信息：{call.excinfo}")
