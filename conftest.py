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
        try:
            shutil.copytree(results_dir, archive_path, dirs_exist_ok=True)
            logger.info(f"📦 历史结果已存档: {archive_path}")
        except FileExistsError:
            logger.warning(f"⚠️ 历史结果已存在，跳过存档: {archive_path}")


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
            try:
                os.remove(db_path)
                logger.info("🧹 数据库文件已清理")
            except PermissionError:
                time.sleep(0.5)
                try:
                    os.remove(db_path)
                    logger.info("🧹 数据库文件已清理（重试成功）")
                except PermissionError:
                    logger.warning("⚠️ 数据库文件被占用，跳过清理")


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


# ==================== Allure 执行者信息（session 级，只写一次） ====================
@pytest.fixture(scope="session", autouse=True)
def allure_executor_info():
    """写入 executor.json，固定内容（整个测试会话只写一次）"""
    os.makedirs("allure-results", exist_ok=True)

    executor = {
        "name": "Local-Dev",
        "type": "local",
        "buildName": "Local-Dev",
        "buildUrl": "",
        "reportName": "ReqRes API自动化报告"
    }
    with open("allure-results/executor.json", "w", encoding="utf-8") as f:
        json.dump(executor, f, ensure_ascii=False, indent=2)


@pytest.fixture(scope="session", autouse=True)
def allure_environment():
    """自动生成 environment.properties（UTF-8 编码，支持中文），整个会话只写一次"""
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
Coverage=文章、商品、订单、评论、用户
"""
    with open("allure-results/environment.properties", "w", encoding="utf-8") as f:
        f.write(env_content)


# ==================== pytest 全局钩子 ====================
def pytest_runtest_setup(item):
    logger.info(f"\n========== 🚀 开始执行用例：{item.nodeid} ==========")


def pytest_runtest_teardown(item):
    logger.info(f"========== ✅ 用例执行结束：{item.nodeid} ==========\n")


# ==================== 测试数据清理增强 ====================
@pytest.fixture(scope="session", autouse=True)
def clean_test_data():
    """测试结束后自动清理并重置数据库"""
    yield

    if ENV_NAME == "dev":
        try:
            logger.info("🧹 开始清理测试数据...")
            init_db()
            logger.info("✅ 数据库已重置，测试数据已清理")
        except Exception as e:
            logger.warning(f"⚠️ 数据清理失败: {e}")


# ==================== 测试用例评分系统 ====================
# 全局变量：存储用例评分数据（供 makereport 和 sessionfinish 共享）
test_scores = {}
test_details = []


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """为每个用例计算评分"""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call":
        test_name = item.nodeid
        duration = getattr(report, 'duration', 0)

        # 基础分 10 分
        score = 10

        if report.passed:
            score += 10
            if hasattr(report, 'rerun_count') and report.rerun_count > 0:
                score += 2
        elif report.failed:
            score -= 5

        # 耗时惩罚（超过 1 秒减分，最多减 5 分）
        if duration > 1.0:
            score -= min(int(duration / 2), 5)

        # 评分范围控制在 0-20
        score = max(0, min(score, 20))

        test_scores[test_name] = score
        test_details.append({
            "name": test_name,
            "score": score,
            "duration": round(duration, 3),
            "status": "PASSED" if report.passed else "FAILED",
            "rerun": getattr(report, 'rerun_count', 0)
        })

        allure.attach(
            f"⭐ 用例评分: {score}/20\n"
            f"⏱️ 耗时: {duration:.3f}s\n"
            f"🔄 重跑次数: {getattr(report, 'rerun_count', 0)}",
            name="用例评分详情",
            attachment_type=allure.attachment_type.TEXT
        )


# ==================== 合并后的 sessionfinish：飞书通知 + 评分报告 ====================
def pytest_sessionfinish(session, exitstatus):
    """测试结束后：1) 发送飞书通知 2) 生成评分报告"""

    # ---------- 1. 飞书通知 ----------
    try:
        from common.feishu_notify import send_feishu_message

        total = session.testscollected
        reporter = session.config.pluginmanager.get_plugin("terminalreporter")

        if reporter is None:
            logger.warning("⚠️ 无法获取测试结果统计，跳过飞书通知")
        else:
            passed = len(reporter.stats.get('passed', []))
            failed = len(reporter.stats.get('failed', []))
            skipped = len(reporter.stats.get('skipped', []))
            errors = len(reporter.stats.get('error', []))

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
    except Exception as e:
        logger.warning(f"⚠️ 飞书通知发送失败: {e}")

    # ---------- 2. 评分报告 ----------
    if test_details:
        score_report = "📊 测试用例评分报告\n" + "=" * 50 + "\n\n"
        sorted_details = sorted(test_details, key=lambda x: x["score"], reverse=True)

        for i, detail in enumerate(sorted_details, 1):
            status_icon = "✅" if detail["status"] == "PASSED" else "❌"
            score_bar = "⭐" * (detail["score"] // 2) + "☆" * ((20 - detail["score"]) // 2)
            score_report += f"{i:2d}. {status_icon} {detail['score']:2d}/20 {score_bar}\n"
            score_report += f"    📝 {detail['name']}\n"
            score_report += f"    ⏱️ 耗时: {detail['duration']:.3f}s"
            if detail['rerun'] > 0:
                score_report += f" | 🔄 重跑: {detail['rerun']}次"
            score_report += "\n\n"

        total = len(sorted_details)
        avg_score = sum(d["score"] for d in sorted_details) / total if total > 0 else 0
        score_report += "=" * 50 + "\n"
        score_report += f"📊 总用例数: {total}\n"
        score_report += f"📈 平均评分: {avg_score:.1f}/20\n"
        score_report += f"🏆 最高分: {max(d['score'] for d in sorted_details)}/20\n"
        score_report += f"📉 最低分: {min(d['score'] for d in sorted_details)}/20\n"
        score_report += f"⏱️ 最慢用例: {max(d['duration'] for d in sorted_details):.3f}s\n"

        os.makedirs("reports", exist_ok=True)
        with open("reports/test_scores.txt", "w", encoding="utf-8") as f:
            f.write(score_report)

        logger.info(f"📊 测试评分报告已生成: reports/test_scores.txt")
        logger.info(f"📈 平均评分: {avg_score:.1f}/20")


# ==================== 终端输出评分摘要 ====================
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """在终端输出评分摘要"""
    if test_details:
        total = len(test_details)
        avg_score = sum(d["score"] for d in test_details) / total if total > 0 else 0
        passed = len([d for d in test_details if d["status"] == "PASSED"])

        terminalreporter.write_sep("=", "📊 测试评分摘要")
        terminalreporter.write_line(f"  总用例: {total}")
        terminalreporter.write_line(f"  通过: {passed}")
        terminalreporter.write_line(f"  失败: {total - passed}")
        terminalreporter.write_line(f"  平均评分: {avg_score:.1f}/20")
        terminalreporter.write_line(f"  评分报告: reports/test_scores.txt")