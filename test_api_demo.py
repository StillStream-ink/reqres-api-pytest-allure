import pytest
import requests
import allure
from common.yaml_util import read_yaml
from common.log_util import logger
from common.assert_util import *

BASE_URL = "https://jsonplaceholder.typicode.com"

# ---------------------- 公共封装函数（超时、异常捕获、重试）----------------------
def send_request(method, url, params=None, json_data=None, timeout=10):
    """
    封装统一发送http请求，增加超时、异常捕获
    :param method: 请求方式 GET / POST / PUT / DELETE
    :param url: 接口地址
    :param params: get查询参数
    :param json_data: post/put的body数据
    :param timeout: 超时时间，默认10秒
    :return: response对象；发生网络异常返回None
    """
    import time
    retry_max = 2
    for i in range(1, retry_max + 1):
        try:
            from conftest import global_headers
            resp = requests.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                headers=global_headers,
                timeout=timeout
            )
            return resp
        except requests.exceptions.Timeout:
            print(f"\n【请求超时】第{i}次重试，url:{url}")
        except requests.exceptions.ConnectionError:
            print(f"\n【连接失败】第{i}次重试，url:{url}")
        except Exception as e:
            print(f"\n【未知异常】{str(e)}")
        time.sleep(1)
    return None


# ---------------------- 测试用例 ----------------------
@allure.feature("文章模块")
@allure.story("获取文章列表")
def test_get_post_list():
    """GET 请求：获取文章列表"""
    url = f"{BASE_URL}/posts"
    resp = send_request(method="GET", url=url)
    assert_http_response(resp, 200)
    body = resp.json()
    assert isinstance(body, list), "❌ 接口返回数据不是数组"
    assert_json_key_exists(body[0], "id")
    assert_json_key_exists(body[0], "title")


@allure.feature("文章模块")
@allure.story("获取单篇文章")
def test_get_single_post():
    """GET 请求：获取单篇文章id=1"""
    url = f"{BASE_URL}/posts/1"
    resp = send_request("GET", url=url)
    assert_http_response(resp, 200)
    body = resp.json()
    assert_json_value_equal(body, "id", 1)
    assert_json_type(body, "title", str)
    assert_json_type(body, "userId", int)


@allure.feature("文章模块")
@allure.story("参数化查询文章")
@pytest.mark.parametrize("post_id", [1, 2, 3, 4])
def test_get_post_param(post_id):
    """参数化：传入不同文章id获取数据"""
    url = f"{BASE_URL}/posts/{post_id}"
    resp = send_request("GET", url=url)
    assert_http_response(resp, 200)
    body = resp.json()
    assert_json_value_equal(body, "id", post_id)
    assert_json_type(body, "title", str)


@allure.feature("文章模块")
@allure.story("新增文章")
def test_create_post():
    """POST：新增文章"""
    url = f"{BASE_URL}/posts"
    json_data = {
        "title": "自动化测试文章",
        "body": "接口自动化demo",
        "userId": 1
    }
    resp = send_request("POST", url=url, json_data=json_data)
    assert_http_response(resp, 201)
    body = resp.json()
    assert_json_value_equal(body, "title", "自动化测试文章")
    assert_json_key_exists(body, "id")


@allure.feature("文章模块")
@allure.story("修改文章")
def test_update_post():
    """PUT：更新文章"""
    url = f"{BASE_URL}/posts/1"
    json_data = {
        "title": "更新后的标题",
        "body": "修改内容",
        "userId": 1
    }
    resp = send_request("PUT", url=url, json_data=json_data)
    assert_http_response(resp, 200)
    body = resp.json()
    assert_json_value_equal(body, "title", "更新后的标题")


@allure.feature("文章模块")
@allure.story("删除文章")
def test_delete_post():
    """DELETE：删除文章"""
    url = f"{BASE_URL}/posts/1"
    resp = send_request("DELETE", url=url)
    assert_http_response(resp, 200)


@allure.feature("用户模块")
@allure.story("需要token鉴权的用户信息查询")
def test_get_user_info(user_token):
    """注入user_token，send_request自动带上Authorization头部"""
    url = f"{BASE_URL}/users/2"
    resp = send_request("GET", url=url)
    assert_http_response(resp, 200)
    body = resp.json()
    assert_json_value_equal(body, "id", 2)
    assert_json_key_exists(body, "name")
