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

# ---------------------- 导入本地 Mock 服务 ----------------------
# 如果 mock_server.py 放在根目录，用这个：
from common.mock_server import app, init_db
# 如果 mock_server.py 放在 common/ 目录，注释上面，用下面这个：
# from common.mock_server import app, init_db

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
        'use_reloader': False
    })
    server.daemon = True
    server.start()
    time.sleep(1.5)  # 等待服务启动
    yield
    # 测试结束后清理数据库文件
    db_path = os.path.join(os.path.dirname(__file__), 'test_mock.db')
    if os.path.exists(db_path):
        os.remove(db_path)

# ---------------------- 原有 Fixture ----------------------
@pytest.fixture(scope="function")
def get_new_post_id():
    """前置fixture：新增文章，返回post_id；后置自动删除清理资源"""
    from test_api_demo import send_request, BASE_URL
    create_body = {"title": "fixture依赖演示", "body": "fixture解耦接口依赖", "userId": 1}
    resp = send_request("POST", f"{BASE_URL}/posts", json_data=create_body)
    assert resp.status_code == 201
    post_id = resp.json()["id"]
    yield post_id
    # 后置：自动清理数据
    send_request("DELETE", f"{BASE_URL}/posts/{post_id}")

@pytest.fixture(scope="module")
def user_token():
    """模拟登录，直接生成假token，演示全局自动注入header"""
    from test_api_demo import send_request, BASE_URL
    logger.info("==== 模拟登录前置，生成测试token ====")
    token = "mock-test-token-123456"
    global global_headers
    global_headers["Authorization"] = f"Bearer {token}"
    yield token
    global_headers.clear()

# ---------------------- Allure报告全局钩子 ----------------------
@pytest.fixture(autouse=True)
def allure_env_info():
    """自动写入Allure环境信息"""
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