# -*- coding: utf-8 -*-
import pytest
import threading
import time
import sys
import os
import json
import requests
import platform
import allure
import shutil
from datetime import datetime
from common.feishu_notify import send_feishu_message


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common.yaml_util import read_yaml
from common.log_util import logger
from common.mock_server import app, init_db
from common.config_util import ENV_CONFIG

BASE_URL = ENV_CONFIG["base_url"]
TIMEOUT = ENV_CONFIG["timeout"]
DB_NAME = ENV_CONFIG["db_name"]
ENV_NAME = ENV_CONFIG["env_name"]

# ==================== 测试报告存档（历史趋势图） ====================
def archive_results():
    """每次运行前把旧结果归档到 history/ 目录"""
    results_dir = "allure-results"
    history_dir = "allure-history"
    if os.path.exists(results_dir):
        os.makedirs(history_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_path = os.path.join(history_dir, timestamp)
        shutil.copytree(results_dir, archive_path)
        logger.info(f"📦 历史结果已存档: {archive_path}")

# 在 session 开始时执行归档
archive_results()

# ==================== 自动启动 Mock 服务 ====================
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

# ==================== 全局 Fixtures ====================
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

# ==================== Allure 执行者信息 ====================
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
Coverage=文章、商品、订单、用户、MySQL集成测试
"""
    with open("allure-results/environment.properties", "w", encoding="utf-8") as f:
        f.write(env_content)

# ==================== pytest 全局钩子 ====================
def pytest_runtest_setup(item):
    # 初始化 item 上的请求/响应存储
    item._last_request = None
    item._last_response = None
    logger.info(f"\n========== 🚀 开始执行用例：{item.nodeid} ==========")

def pytest_runtest_teardown(item):
    logger.info(f"========== ✅ 用例执行结束：{item.nodeid} ==========\n")
    if hasattr(item, '_last_request'):
        delattr(item, '_last_request')
    if hasattr(item, '_last_response'):
        delattr(item, '_last_response')

def pytest_runtest_makereport(item, call):
    if call.when == "call" and call.excinfo is not None:
        logger.error(f"❌ 用例失败：{item.nodeid}，错误信息：{call.excinfo}")

        # 失败时自动保存请求/响应到 Allure 附件
        last_req = getattr(item, '_last_request', None)
        last_resp = getattr(item, '_last_response', None)

        if last_req:
            allure.attach(
                f"URL: {last_req.get('url')}\nMethod: {last_req.get('method')}\nHeaders: {last_req.get('headers')}\nBody: {last_req.get('body')}",
                name="失败时请求详情",
                attachment_type=allure.attachment_type.TEXT
            )
        if last_resp:
            allure.attach(
                f"Status: {last_resp.status_code}\nBody: {last_resp.text}",
                name="失败时响应详情",
                attachment_type=allure.attachment_type.TEXT
            )

            # conftest.py 末尾

def pytest_sessionfinish(session, exitstatus):
    """pytest 全部执行完毕后自动调用"""
    # 使用 session 的统计信息
    total = session.testscollected
    
    # 从 reporter 获取测试结果
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    if reporter is None:
        print("⚠️ 无法获取测试结果统计")
        return
    
    passed = len(reporter.stats.get('passed', []))
    failed = len(reporter.stats.get('failed', []))
    skipped = len(reporter.stats.get('skipped', []))
    errors = len(reporter.stats.get('error', []))
    
    # 计算通过率
    executed = passed + failed + errors
    pass_rate = (passed / executed * 100) if executed > 0 else 0

    status = "success" if failed == 0 and errors == 0 else "failure"
    title = "🎉 自动化测试通过" if status == "success" else "❌ 自动化测试失败"
    
    content = f"""**执行结果摘要**
📊 总用例: **{total}**
✅ 通过: **{passed}**
❌ 失败: **{failed}**
⏭️ 跳过: **{skipped}**
⚠️ 错误: **{errors}**
📈 通过率: **{pass_rate:.2f}%**
    """
    
    send_feishu_message(title, content, status)