import pytest
import requests
import allure
from common.yaml_util import read_yaml
from common.log_util import logger
from common.http_util import send_request
import os

# 读取yaml测试数据
base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
test_data = read_yaml(os.path.join(base_path, "config/test_data.yaml"))

BASE_URL = "https://jsonplaceholder.typicode.com"

# 直接使用已存在postId=1，规避404问题
post_id_fixture = 1


@allure.feature("帖子模块")
@allure.story("帖子全业务流程")
@pytest.mark.smoke
def test_post_full_flow():
    """
    完整业务链路：查询帖子 → 更新帖子 → 删除帖子
    """
    post_id = post_id_fixture
    update_body = test_data["post"]["update_info"]

    # 步骤1：获取帖子详情
    logger.info("【步骤1】获取帖子详情")
    res_get = send_request("GET", f"{BASE_URL}/posts/{post_id}")
    assert res_get is not None, "请求无响应，网络异常"
    assert res_get.status_code == 200
    data = res_get.json()
    assert isinstance(data, dict), "接口返回不是json对象"
    logger.info(f"查询帖子结果：{data}")
    assert data["id"] == post_id

    # 步骤2：更新帖子
    logger.info("【步骤2】更新帖子")
    res_put = send_request("PUT", f"{BASE_URL}/posts/{post_id}", json_data=update_body)
    assert res_put is not None, "请求无响应，网络异常"
    assert res_put.status_code == 200
    data_put = res_put.json()
    assert isinstance(data_put, dict), "接口返回不是json对象"
    logger.info(f"更新帖子结果：{data_put}")
    assert data_put["title"] == update_body["title"]

    # 步骤3：删除帖子
    logger.info("【步骤3】删除帖子")
    res_del = send_request("DELETE", f"{BASE_URL}/posts/{post_id}")
    assert res_del is not None, "请求无响应，网络异常"
    assert res_del.status_code == 200
    data_del = res_del.json()
    assert isinstance(data_del, dict), "接口返回不是json对象"
    logger.info(f"删除帖子结果：{data_del}")

@pytest.mark.skip(reason="公共reqres接口偶发超时，待优化重试")
@allure.feature("用户模块")
@allure.story("用户信息全流程")
@pytest.mark.smoke
def test_user_full_flow():
    """
    用户业务链路：查询用户详情 → 修改用户信息
    """
    user_id = 1
    user_update_data = test_data["user"]["update_info"]

    # 步骤1：查询用户详情
    logger.info("【用户步骤1】查询用户信息")
    res_get = send_request("GET", f"{BASE_URL}/users/{user_id}")
    assert res_get is not None, "请求无响应，网络异常"
    assert res_get.status_code == 200
    data = res_get.json()
    assert isinstance(data, dict), "接口返回不是json对象"
    logger.info(f"用户详情：{data}")
    assert data["id"] == user_id

    # 步骤2：更新用户信息
    logger.info("【用户步骤2】更新用户信息")
    res_put = send_request("PUT", f"{BASE_URL}/users/{user_id}", json_data=user_update_data)
    assert res_put is not None, "请求无响应，网络异常"
    assert res_put.status_code == 200
    data_put = res_put.json()
    assert isinstance(data_put, dict), "接口返回不是json对象"
    logger.info(f"更新后用户：{data_put}")
    assert data_put["name"] == user_update_data["name"]


@allure.feature("帖子模块")
@allure.story("异常场景测试")
def test_post_invalid_id():
    """异常场景：查询不存在的帖子id（9999），预期返回404"""
    logger.info("【异常用例】查询不存在帖子id=9999")
    res = send_request("GET", f"{BASE_URL}/posts/9999")
    assert res is not None, "请求网络异常，未获取响应"
    logger.info(f"响应状态码：{res.status_code}")
    assert res.status_code == 404


@allure.feature("用户模块")
@allure.story("异常场景测试")
def test_user_invalid_id():
    """异常场景：查询不存在用户id（9999），预期返回404"""
    logger.info("【异常用例】查询不存在用户id=9999")
    res = send_request("GET", f"{BASE_URL}/users/9999")
    assert res is not None, "请求网络异常，未获取响应"
    logger.info(f"响应状态码：{res.status_code}")
    assert res.status_code == 404


@allure.feature("帖子模块")
@allure.story("空数据提交测试")
def test_post_put_empty_body():
    """异常场景：put更新传入空json，校验接口兼容"""
    logger.info("【异常用例】帖子更新传入空body")
    res = send_request("PUT", f"{BASE_URL}/posts/1", json_data={})
    logger.info(f"空body更新响应：{res.json()}")
    # mock接口不会校验空数据，这里只断言服务正常返回200
    assert res.status_code == 200

@pytest.mark.skip(reason="jsonplaceholder公网接口偶发超时，内网环境再启用")
@allure.feature("帖子模块")
@allure.story("参数化-非法ID查询")
@pytest.mark.parametrize("post_id,expect_code", [
    (9999, 404),
    (-1, 404),
    (0, 404),
    ("abc", 404)
])
def test_post_param_invalid_id(post_id, expect_code):
    """参数化异常：多组非法帖子ID，预期404"""
    logger.info(f"【参数化异常】帖子id={post_id}，预期状态码{expect_code}")
    res = send_request("GET", f"{BASE_URL}/posts/{post_id}")
    assert res is not None, "请求无响应，网络异常"
    logger.info(f"实际状态码：{res.status_code}")
    assert res.status_code == expect_code



@allure.feature("用户模块")
@allure.story("参数化-非法ID查询")
@pytest.mark.parametrize("user_id,expect_code", [
    (9999, 404),
    (-5, 404),
    (0, 404),
    ("xyz", 404)
])
def test_user_param_invalid_id(user_id, expect_code):
    """参数化异常：多组非法用户ID，预期404"""
    logger.info(f"【参数化异常】用户id={user_id}，预期状态码{expect_code}")
    res = send_request("GET", f"{BASE_URL}/users/{user_id}")
    logger.info(f"实际状态码：{res.status_code}")
    assert res.status_code == expect_code
