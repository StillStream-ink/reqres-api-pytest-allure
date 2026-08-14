import pytest
import requests
import os
from common.yaml_util import read_yaml
from common.log_util import logger
from common.db_util import DBUtil
import allure

# 读取yaml测试数据
base_path = os.path.abspath(".")
test_data = read_yaml(os.path.join(base_path, "config/test_data.yaml"))
BASE_URL = "https://jsonplaceholder.typicode.com"


# ========== 【注释】jsonplaceholder无登录接口，暂时屏蔽token登录fixture ==========
# @pytest.fixture(scope="module")
# def user_token():
#     """
#     前置Fixture：登录获取token，整个模块只执行一次
#     yield 把token传给下游用例
#     """
#     login_data = test_data["login"]["normal"]
#     url = f"{BASE_URL}/login"
#     logger.info("==== 执行前置：用户登录 ====")
#     resp = requests.post(url, json=login_data)
#     logger.info(f"登录响应：{resp.json()}")
#     assert resp.status_code == 200
#     token = resp.json()["token"]
#     yield token


# ========== 【注释】该用例依赖token，jsonplaceholder无鉴权接口，先注释 ==========
# @allure.feature("用户模块")
# @allure.story("获取用户信息")
# def test_get_user_info(user_token):
#     """GET 请求：获取用户信息，携带token鉴权"""
#     logger.info("==== 开始执行用例：test_get_user_info ====")
#     headers = {"Authorization": f"Bearer {user_token}"}
#     resp = requests.get(f"{BASE_URL}/users/1", headers=headers)
#     logger.info(f"接口响应：{resp.json()}")
#     assert resp.status_code == 200
#     assert resp.json()["id"] == 1
#     logger.info("==== 用例执行结束：test_get_user_info ====")


@pytest.fixture(scope="module")
def new_post_id():
    """前置Fixture：新增文章，拿到动态ID，给查询/修改/删除用例复用"""
    logger.info("==== Fixture前置：创建测试文章 ====")
    json_body = {
        "title": "自动化前置文章",
        "body": "fixture生成",
        "userId": 1
    }
    resp = requests.post(f"{BASE_URL}/posts", json=json_body)
    assert resp.status_code == 201
    res_json = resp.json()
    yield res_json["id"]


@allure.feature("文章模块")
@allure.story("获取文章列表")
def test_get_post_list():
    """GET 请求：获取文章列表"""
    logger.info("==== 开始执行用例：test_get_post_list ====")
    resp = requests.get(f"{BASE_URL}/posts")
    logger.info(f"接口响应长度：{len(resp.json())}")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    logger.info("==== 用例执行结束：test_get_post_list ====")

@pytest.mark.xfail(reason="jsonplaceholder不持久化POST新增资源，CI环境会404，本地会话内正常")
@allure.feature("文章模块")
@allure.story("获取单篇文章")
def test_get_single_post(new_post_id):
    """GET 请求：获取【动态生成】的单篇文章"""
    logger.info(f"==== 开始执行用例：test_get_single_post post_id={new_post_id} ====")
    resp = requests.get(f"{BASE_URL}/posts/{new_post_id}")
    logger.info(f"接口响应：{resp.json()}")
    assert resp.status_code == 200
    assert resp.json()["id"] == new_post_id
    logger.info("==== 用例执行结束：test_get_single_post ====")

@pytest.mark.xfail(reason="jsonplaceholder不持久化POST新增资源，CI环境会404，本地会话内正常")
@allure.feature("文章模块")
@allure.story("参数化查询文章")
@pytest.mark.parametrize("post_offset", [1,2])
def test_get_post_param(new_post_id, post_offset):
    """参数化：基于动态id演示"""
    post_id = new_post_id
    logger.info(f"==== 开始执行用例：test_get_post_param post_id={post_id} ====")
    resp = requests.get(f"{BASE_URL}/posts/{post_id}")
    logger.info(f"查询文章id={post_id}, 标题：{resp.json()['title']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == post_id
    logger.info(f"==== 用例执行结束：test_get_post_param post_id={post_id} ====")


@allure.feature("文章模块")
@allure.story("新增文章")
def test_create_post():
    """POST 请求：新增文章"""
    logger.info("==== 开始执行用例：test_create_post ====")
    json_body = {
        "title": "测试自动化新增文章",
        "body": "接口自动化测试内容",
        "userId": 1
    }
    resp = requests.post(f"{BASE_URL}/posts", json=json_body)
    logger.info(f"接口响应：{resp.json()}")
    assert resp.status_code == 201
    assert resp.json()["title"] == json_body["title"]
    logger.info("==== 用例执行结束：test_create_post ====")

@pytest.mark.xfail(reason="jsonplaceholder不持久化POST新增资源，CI环境会404，本地会话内正常")
@allure.feature("文章模块")
@allure.story("修改文章")
def test_update_post(new_post_id):
    """PUT 请求：修改【动态生成】的文章"""
    logger.info(f"==== 开始执行用例：test_update_post post_id={new_post_id} ====")
    json_body = {
        "title": "修改后的文章标题",
        "body": "修改后的正文",
        "userId": 1
    }
    resp = requests.put(f"{BASE_URL}/posts/{new_post_id}", json=json_body)
    logger.info(f"接口响应：{resp.json()}")
    assert resp.status_code == 200
    assert resp.json()["title"] == json_body["title"]
    logger.info("==== 用例执行结束：test_update_post ====")


@pytest.mark.skip(reason="flask服务暂未实现DELETE接口，待后端补充")
@allure.feature("文章模块")
@allure.story("删除文章")
def test_delete_post(new_post_id):
    """DELETE 请求：删除【动态生成】的文章"""
    logger.info(f"==== 开始执行用例：test_delete_post post_id={new_post_id} ====")
    resp = requests.delete(f"{BASE_URL}/posts/{new_post_id}")
    logger.info(f"接口状态码：{resp.status_code}")
    assert resp.status_code == 200
    logger.info("==== 用例执行结束：test_delete_post ====")


# ====================== 数据库校验用例【注释保存，后续搭MySQL再启用】 ======================
@pytest.mark.xfail(reason="jsonplaceholder为mock服务，不会真实落库，用于演示接口+DB双校验模板")
@allure.feature("文章模块")
@allure.story("新增文章-接口+数据库校验")
def test_create_post_check_db(db_conn):
    """新增文章，同时校验数据库数据"""
    logger.info("==== 开始执行用例：test_create_post_check_db ====")
    json_body = {
        "title": "DB校验-新增文章",
        "body": "接口落库校验",
        "userId": 1
    }
    resp = requests.post(f"{BASE_URL}/posts", json=json_body)
    logger.info(f"接口响应：{resp.json()}")
    assert resp.status_code == 201
    post_id = resp.json()["id"]

    # 查询数据库校验
    sql = f"select * from posts where id={post_id}"
    db_res = db_conn.query_one(sql)
    assert db_res["title"] == json_body["title"]
    logger.info("==== 用例执行结束：test_create_post_check_db ====")

@pytest.mark.xfail(reason="jsonplaceholder为mock服务，不会真实落库，用于演示接口+DB双校验模板")
@allure.feature("文章模块")
@allure.story("修改文章-接口+数据库校验")
def test_update_post_check_db(db_conn):
    """修改文章，校验数据库"""
    logger.info("==== 开始执行用例：test_update_post_check_db ====")
    json_body = {
        "title": "DB校验-更新标题",
        "body": "更新落库校验",
        "userId": 1
    }
    resp = requests.put(f"{BASE_URL}/posts/1", json=json_body)
    logger.info(f"接口响应：{resp.json()}")
    assert resp.status_code == 200

    # 查询数据库校验
    sql = "select * from posts where id=1"
    db_res = db_conn.query_one(sql)
    assert db_res["title"] == json_body["title"]
    logger.info("==== 用例执行结束：test_update_post_check_db ====")


@pytest.fixture(scope="function")
def db_conn():
    """数据库连接fixture，每个用例执行前后自动创建/关闭连接"""
    # ✅ 在fixture内部读取yaml，解决变量作用域NameError
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_data = read_yaml(os.path.join(base_path, "config/test_data.yaml"))

    db = DBUtil(
        host=test_data["db"]["host"],
        user=test_data["db"]["user"],
        password=test_data["db"]["pwd"],
        database=test_data["db"]["db"],
        port=test_data["db"]["port"]
    )
    yield db
    db.close()
