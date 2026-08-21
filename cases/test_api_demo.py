import pytest
import requests
import os
import sqlite3
import pymysql
from common.yaml_util import read_yaml
from common.log_util import logger
from common.config_util import ENV_CONFIG
from common.mock_server import DB_PATH
from common.mock_server import DB_CONFIG
import allure

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
test_data = read_yaml(os.path.join(base_path, "config/test_data.yaml"))

BASE_URL = ENV_CONFIG["base_url"]
TIMEOUT = ENV_CONFIG["timeout"]
DB_NAME = ENV_CONFIG["db_name"]


@pytest.fixture(scope="function")
def new_post_id():
    """前置Fixture：新增文章，拿到动态ID（function级别，用完即删）"""
    logger.info("==== Fixture前置：创建测试文章 ====")
    json_body = {"title": "自动化前置文章", "body": "fixture生成", "userId": 1}
    resp = requests.post(f"{BASE_URL}/posts", json=json_body, timeout=TIMEOUT)
    assert resp.status_code == 201
    res_json = resp.json()
    post_id = res_json["id"]
    yield post_id
    try:
        requests.delete(f"{BASE_URL}/posts/{post_id}", timeout=TIMEOUT)
        logger.info(f"==== Fixture清理：删除文章 {post_id} ====")
    except Exception as e:
        logger.warning(f"清理文章 {post_id} 失败: {e}")


@allure.suite("文章模块")
class TestPostAPI:
    """文章相关接口测试"""

    @allure.feature("文章模块")
    @allure.story("获取文章列表")
    def test_get_post_list(self):
        with allure.step("发送GET请求获取文章列表"):
            resp = requests.get(f"{BASE_URL}/posts", timeout=TIMEOUT)
            allure.attach(resp.text, "响应结果", allure.attachment_type.JSON)

        with allure.step("断言校验"):
            assert resp.status_code == 200
            assert isinstance(resp.json(), list)
            assert len(resp.json()) >= 2

    @allure.feature("文章模块")
    @allure.story("获取单篇文章")
    def test_get_single_post(self, new_post_id):
        with allure.step(f"发送GET请求查询文章ID={new_post_id}"):
            resp = requests.get(f"{BASE_URL}/posts/{new_post_id}", timeout=TIMEOUT)
            allure.attach(resp.text, "响应结果", allure.attachment_type.JSON)

        with allure.step("断言校验"):
            assert resp.status_code == 200
            assert resp.json()["id"] == new_post_id

    @allure.feature("文章模块")
    @allure.story("参数化查询文章")
    @pytest.mark.parametrize("post_id", [1, 2])
    def test_get_post_param(self, post_id):
        with allure.step(f"发送GET请求查询文章ID={post_id}"):
            resp = requests.get(f"{BASE_URL}/posts/{post_id}", timeout=TIMEOUT)
            allure.attach(resp.text, "响应结果", allure.attachment_type.JSON)

        with allure.step("断言校验"):
            assert resp.status_code == 200
            assert resp.json()["id"] == post_id

    @allure.feature("文章模块")
    @allure.story("新增文章")
    def test_create_post(self):
        with allure.step("构造请求参数"):
            json_body = {
                "title": "测试自动化新增文章",
                "body": "接口自动化测试内容",
                "userId": 1
            }
            allure.attach(str(json_body), "请求参数", allure.attachment_type.JSON)

        with allure.step("发送POST请求"):
            resp = requests.post(f"{BASE_URL}/posts", json=json_body, timeout=TIMEOUT)
            allure.attach(resp.text, "响应结果", allure.attachment_type.JSON)

        with allure.step("断言校验"):
            assert resp.status_code == 201
            assert resp.json()["title"] == json_body["title"]
            assert "id" in resp.json()

    @allure.feature("文章模块")
    @allure.story("修改文章")
    def test_update_post(self, new_post_id):
        with allure.step("构造更新参数"):
            json_body = {
                "title": "修改后的文章标题",
                "body": "修改后的正文",
                "userId": 1
            }
            allure.attach(str(json_body), "请求参数", allure.attachment_type.JSON)

        with allure.step(f"发送PUT请求修改文章ID={new_post_id}"):
            resp = requests.put(f"{BASE_URL}/posts/{new_post_id}", json=json_body, timeout=TIMEOUT)
            allure.attach(resp.text, "响应结果", allure.attachment_type.JSON)

        with allure.step("断言校验"):
            assert resp.status_code == 200
            assert resp.json()["title"] == json_body["title"]

    @allure.feature("文章模块")
    @allure.story("删除文章")
    def test_delete_post(self):
        with allure.step("前置：创建待删除文章"):
            payload = {"title": "to be deleted", "body": "delete me", "userId": 1}
            create_resp = requests.post(f"{BASE_URL}/posts", json=payload, timeout=TIMEOUT)
            post_id = create_resp.json()["id"]
            allure.attach(f"待删除文章ID: {post_id}", "前置数据")

        with allure.step(f"发送DELETE请求删除文章ID={post_id}"):
            resp = requests.delete(f"{BASE_URL}/posts/{post_id}", timeout=TIMEOUT)
            allure.attach(f"状态码: {resp.status_code}", "删除响应")
            assert resp.status_code == 200

        with allure.step("验证文章已删除"):
            get_resp = requests.get(f"{BASE_URL}/posts/{post_id}", timeout=TIMEOUT)
            allure.attach(f"查询状态码: {get_resp.status_code}", "验证响应")
            assert get_resp.status_code == 404

    @allure.feature("文章模块")
    @allure.story("新增文章-接口+数据库校验")
    def test_create_post_check_db(self):
        with allure.step("Step1: 调用接口新增文章"):
            json_body = {
                "title": "DB校验-新增文章",
                "body": "接口落库校验",
                "userId": 1
            }
            allure.attach(str(json_body), "请求参数", allure.attachment_type.JSON)
            resp = requests.post(f"{BASE_URL}/posts", json=json_body, timeout=TIMEOUT)
            allure.attach(resp.text, "接口响应", allure.attachment_type.JSON)
            assert resp.status_code == 201
            post_id = resp.json()["id"]
            allure.attach(f"新增文章ID: {post_id}", "提取ID")

        with allure.step("Step2: 查询数据库校验落库"):
            conn = pymysql.connect(**DB_CONFIG)
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT title, body FROM posts WHERE id = %s", (post_id,))
                    row = cursor.fetchone()
                    if row:
                        row_dict = {"title": row[0], "body": row[1]}
                    else:
                        row_dict = None
                    allure.attach(f"DB查询结果: {row_dict}", "数据库记录")
            finally:
                conn.close()

        with allure.step("Step3: 断言接口与DB一致性"):
            assert row_dict is not None, "数据库中未找到新创建的记录"
            assert row_dict["title"] == json_body["title"]
            assert row_dict["body"] == json_body["body"]

    @allure.feature("文章模块")
    @allure.story("修改文章-接口+数据库校验")
    def test_update_post_check_db(self):
        with allure.step("前置：创建测试文章"):
            create_resp = requests.post(f"{BASE_URL}/posts", 
                                        json={"title": "old title", "body": "old body", "userId": 1},
                                        timeout=TIMEOUT)
            post_id = create_resp.json()["id"]
            allure.attach(f"创建文章ID: {post_id}", "前置数据")

        with allure.step("Step1: 调用接口修改文章"):
            json_body = {
                "title": "DB校验-更新标题",
                "body": "更新落库校验",
                "userId": 1
            }
            allure.attach(str(json_body), "请求参数", allure.attachment_type.JSON)
            resp = requests.put(f"{BASE_URL}/posts/{post_id}", json=json_body, timeout=TIMEOUT)
            allure.attach(resp.text, "接口响应", allure.attachment_type.JSON)
            assert resp.status_code == 200

        with allure.step("Step2: 查询数据库校验更新"):
            conn = pymysql.connect(**DB_CONFIG)
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT title, body FROM posts WHERE id = %s", (post_id,))
                row = cursor.fetchone()
                allure.attach(f"DB查询结果: title={row[0]}, body={row[1]}", "数据库记录")
            finally:
                conn.close()

        with allure.step("Step3: 断言接口与DB一致性"):
            assert row is not None, "数据库中未找到该记录"
            assert row[0] == json_body["title"]
            assert row[1] == json_body["body"]

# def test_故意失败():
#     """临时构造失败，用完删掉"""
#     assert False, "故意构造的失败场景"