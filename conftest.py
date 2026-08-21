# -*- coding: utf-8 -*-
import pytest
import threading
import time
import sys
import os
import json
import requests
import platform

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common.yaml_util import read_yaml
from common.log_util import logger
from common.mock_server import app, init_db
from common.config_util import ENV_CONFIG

BASE_URL = ENV_CONFIG["base_url"]
TIMEOUT = ENV_CONFIG["timeout"]
DB_NAME = ENV_CONFIG["db_name"]
ENV_NAME = ENV_CONFIG["env_name"]

# ---------------------- 自动启动 Mock 服务 ----------------------
@pytest.fixture(scope="session", autouse=True)
def live_server():
    """测试会话开始前启动 Flask，结束后自动关闭并清理数据库"""
    if ENV_NAME == "dev":
        init_db()
        server = threading.Thread(target=app.run, kwargs={
            'host': '127.0.0.1',
            'port': 5000,
            'debug': False,
            'use_reloader': False
        })
        server.daemon = True
        server.start()

        start_time = time.time()
        while time.time() - start_time < 10:
            try:
                if requests.get(f"{BASE_URL}/posts", timeout=1).status_code == 200:
                    logger.info(f"✅ Mock 服务已就绪: {BASE_URL}")
                    break
            except requests.ConnectionError:
                time.sleep(0.3)
        else:
            raise RuntimeError("❌ Mock 服务启动超时（10秒），请检查端口 5000 是否被占用")

    yield

    if ENV_NAME == "dev":
        db_path = os.path.join(os.path.dirname(__file__), DB_NAME)
        if os.path.exists(db_path):
            os.remove(db_path)
            logger.info("🧹 数据库文件已清理")

# ---------------------- 全局 Fixtures ----------------------
@pytest.fixture(scope="session")
def base_url():
    return BASE_URL

@pytest.fixture(scope="session")
def api_timeout():
    return TIMEOUT

@pytest.fixture(scope="function")
def new_post_id(base_url, api_timeout):
    logger.info("==== Fixture前置：创建测试文章 ====")
    json_body = {"title": "自动化前置文章", "body": "fixture生成", "userId": 1}
    resp = requests.post(f"{base_url}/posts", json=json_body, timeout=api_timeout)
    assert resp.status_code == 201
    post_id = resp.json()["id"]
    yield post_id
    try:
        requests.delete(f"{base_url}/posts/{post_id}", timeout=api_timeout)
        logger.info(f"==== Fixture清理：删除文章 {post_id} ====")
    except Exception as e:
        logger.warning(f"清理文章 {post_id} 失败: {e}")

@pytest.fixture(scope="session")
def user_token():
    return "mock-token-for-testing" if ENV_NAME == "dev" else "test-token"

# ---------------------- Allure 执行者信息（不写 environment.properties） ----------------------
# ---------------------- Allure 执行者信息 ----------------------
@pytest.fixture(autouse=True)
def allure_executor_info():
    """写入 executor.json，固定内容"""
    os.makedirs("allure-results", exist_ok=True)

    executor = {
        "name": "Jenkins",
        "type": "jenkins",
        "buildName": "Local-Dev",
        "buildUrl": "",
        "reportName": "ReqRes API自动化报告"
    }
    with open("allure-results/executor.json", "w", encoding="utf-8") as f:
        json.dump(executor, f, ensure_ascii=False, indent=2)

@pytest.fixture(autouse=True)
def allure_environment():
    """自动生成 environment.properties（UTF-8 编码，支持中文）"""
    os.makedirs("allure-results", exist_ok=True)

    env_content = f"""Project=ReqRes接口自动化测试
BaseUrl={BASE_URL}
Environment={ENV_NAME}
Timeout={TIMEOUT}
Framework=pytest
Python={platform.python_version()}
System={platform.system()} {platform.release()}
Executor=Local-Dev
TestDesign=等价类划分、边界值分析、场景法
Coverage=文章、用户、帖子、MySQL集成测试
"""
    with open("allure-results/environment.properties", "w", encoding="utf-8") as f:
        f.write(env_content)
# ---------------------- pytest 全局钩子 ----------------------
def pytest_runtest_setup(item):
    logger.info(f"\n========== 🚀 开始执行用例：{item.nodeid} ==========")

def pytest_runtest_teardown(item):
    logger.info(f"========== ✅ 用例执行结束：{item.nodeid} ==========\n")

def pytest_runtest_makereport(item, call):
    if call.when == "call" and call.excinfo is not None:
        logger.error(f"❌ 用例失败：{item.nodeid}，错误信息：{call.excinfo}")