import allure
import pytest
from common.yaml_util import read_yaml
from common.log_util import logger
import os
# 全局存储公共请求头
global_headers = {}
# ---------------------- 全局Fixture（所有测试文件直接用，无需import） ----------------------
@pytest.fixture(scope="function")
def get_new_post_id():
    """前置fixture：新增文章，返回post_id；后置自动删除清理资源（teardown）"""
    from test_api_demo import send_request, BASE_URL
    create_body = {"title":"fixture依赖演示","body":"fixture解耦接口依赖","userId":1}
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
    # 模拟拿到token，不用请求接口
    token = "mock-test-token-123456"
    # ✅ 写入全局header
    global global_headers
    global_headers["Authorization"] = f"Bearer {token}"
    yield token
    # 后置清理：清空header
    global_headers.clear()


# ---------------------- Allure报告全局钩子（自动注入环境信息，解决你之前环境空白问题！） ----------------------
@pytest.fixture(autouse=True)
def allure_env_info():
    """自动写入Allure环境信息，兼容新版allure-pytest"""
    import os
    env_content = """python_version=3.11.5
pytest_version=7.4.4
project=Reqres接口自动化
base_url=https://jsonplaceholder.typicode.com
"""
    # 写入allure-results下的环境文件
    result_path = "allure-results/environment.properties"
    # 先确保目录存在
    if not os.path.exists("allure-results"):
        os.makedirs("allure-results")
    with open(result_path, "w", encoding="utf-8") as f:
        f.write(env_content)


# ---------------------- pytest全局钩子示例：用例执行前后打印日志 ----------------------
def pytest_runtest_setup(item):
    """每个用例执行前触发"""
    logger.info(f"\n========== 开始执行用例：{item.nodeid} ==========")

def pytest_runtest_teardown(item):
    """每个用例执行完成后触发"""
    logger.info(f"========== 用例执行结束：{item.nodeid} ==========\n")

def pytest_runtest_makereport(item, call):
    """捕获用例失败，自动截图/保存请求日志（接口项目可保存响应体到allure附件）"""
    if call.when == "call" and call.excinfo is not None:
        logger.error(f"❌ 用例失败：{item.nodeid}，错误信息：{call.excinfo}")
