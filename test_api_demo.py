import pytest
import requests
import os
import sqlite3
from common.yaml_util import read_yaml
from common.log_util import logger
import allure

base_path = os.path.abspath(".")
test_data = read_yaml(os.path.join(base_path, "config/test_data.yaml"))
BASE_URL = "http://127.0.0.1:5000"


@pytest.fixture(scope="module")
def new_post_id():
    """前置Fixture：新增文章，拿到动态ID"""
    logger.info("==== Fixture前置：创建测试文章 ====")
    json_body = {"title": "自动化前置文章", "body": "fixture生成", "userId": 1}
    resp = requests.post(f"{BASE_URL}/posts", json=json_body)
    assert resp.status_code == 201
    res_json = resp.json()
    yield res_json["id"]
    requests.delete(f"{BASE_URL}/posts/{res_json['id']}")


@pytest.fixture(scope="function")
def db_conn():
    """数据库连接fixture"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_mock.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


# ====================== 接口测试用例 ======================

@allure.feature("文章模块")
@allure.story("获取文章列表")
def test_get_post_list():
    with allure.step("发送GET请求获取文章列表"):
        resp = requests.get(f"{BASE_URL}/posts")
        allure.attach(resp.text, "响应结果", allure.attachment_type.JSON)
    
    with allure.step("断言校验"):
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) >= 2


@allure.feature("文章模块")
@allure.story("获取单篇文章")
def test_get_single_post(new_post_id):
    with allure.step(f"发送GET请求查询文章ID={new_post_id}"):
        resp = requests.get(f"{BASE_URL}/posts/{new_post_id}")
        allure.attach(resp.text, "响应结果", allure.attachment_type.JSON)
    
    with allure.step("断言校验"):
        assert resp.status_code == 200
        assert resp.json()["id"] == new_post_id


@allure.feature("文章模块")
@allure.story("参数化查询文章")
@pytest.mark.parametrize("post_id", [1, 2])
def test_get_post_param(post_id):
    with allure.step(f"发送GET请求查询文章ID={post_id}"):
        resp = requests.get(f"{BASE_URL}/posts/{post_id}")
        allure.attach(resp.text, "响应结果", allure.attachment_type.JSON)
    
    with allure.step("断言校验"):
        assert resp.status_code == 200
        assert resp.json()["id"] == post_id


<<<<<<< HEAD
=======

>>>>>>> b8cf692 (ci: add quality gate and github actions workflow)
@allure.feature("文章模块")
@allure.story("新增文章")
def test_create_post():
    with allure.step("构造请求参数"):
        json_body = {
            "title": "测试自动化新增文章",
            "body": "接口自动化测试内容",
            "userId": 1
        }
        allure.attach(str(json_body), "请求参数", allure.attachment_type.JSON)
    
    with allure.step("发送POST请求"):
        resp = requests.post(f"{BASE_URL}/posts", json=json_body)
        allure.attach(resp.text, "响应结果", allure.attachment_type.JSON)
    
    with allure.step("断言校验"):
        assert resp.status_code == 201
        assert resp.json()["title"] == json_body["title"]
        assert "id" in resp.json()

@pytest.mark.xfail(reason="jsonplaceholder不持久化POST新增资源，CI环境会404，本地会话内正常")
@allure.feature("文章模块")
@allure.story("修改文章")
def test_update_post(new_post_id):
    with allure.step("构造更新参数"):
        json_body = {
            "title": "修改后的文章标题",
            "body": "修改后的正文",
            "userId": 1
        }
        allure.attach(str(json_body), "请求参数", allure.attachment_type.JSON)
    
    with allure.step(f"发送PUT请求修改文章ID={new_post_id}"):
        resp = requests.put(f"{BASE_URL}/posts/{new_post_id}", json=json_body)
        allure.attach(resp.text, "响应结果", allure.attachment_type.JSON)
    
    with allure.step("断言校验"):
        assert resp.status_code == 200
        assert resp.json()["title"] == json_body["title"]


@allure.feature("文章模块")
@allure.story("删除文章")
def test_delete_post():
    with allure.step("前置：创建待删除文章"):
        payload = {"title": "to be deleted", "body": "delete me", "userId": 1}
        create_resp = requests.post(f"{BASE_URL}/posts", json=payload)
        post_id = create_resp.json()["id"]
        allure.attach(f"待删除文章ID: {post_id}", "前置数据")
    
    with allure.step(f"发送DELETE请求删除文章ID={post_id}"):
        resp = requests.delete(f"{BASE_URL}/posts/{post_id}")
        allure.attach(f"状态码: {resp.status_code}", "删除响应")
        assert resp.status_code == 200
    
    with allure.step("验证文章已删除"):
        get_resp = requests.get(f"{BASE_URL}/posts/{post_id}")
        allure.attach(f"查询状态码: {get_resp.status_code}", "验证响应")
        assert get_resp.status_code == 404


# ====================== 数据库双检用例 ======================

@allure.feature("文章模块")
@allure.story("新增文章-接口+数据库校验")
def test_create_post_check_db(db_conn):
    with allure.step("Step1: 调用接口新增文章"):
        json_body = {
            "title": "DB校验-新增文章",
            "body": "接口落库校验",
            "userId": 1
        }
        allure.attach(str(json_body), "请求参数", allure.attachment_type.JSON)
        resp = requests.post(f"{BASE_URL}/posts", json=json_body)
        allure.attach(resp.text, "接口响应", allure.attachment_type.JSON)
        assert resp.status_code == 201
        post_id = resp.json()["id"]
        allure.attach(f"新增文章ID: {post_id}", "提取ID")
    
    with allure.step("Step2: 查询数据库校验落库"):
        cursor = db_conn.cursor()
        cursor.execute("SELECT title, body FROM posts WHERE id = ?", (post_id,))
        row = cursor.fetchone()
        allure.attach(f"DB查询结果: title={row['title']}, body={row['body']}", "数据库记录")
    
    with allure.step("Step3: 断言接口与DB一致性"):
        assert row is not None, "数据库中未找到新创建的记录"
        assert row["title"] == json_body["title"]
        assert row["body"] == json_body["body"]


@allure.feature("文章模块")
@allure.story("修改文章-接口+数据库校验")
def test_update_post_check_db(db_conn):
    with allure.step("前置：创建测试文章"):
        create_resp = requests.post(f"{BASE_URL}/posts", 
                                    json={"title": "old title", "body": "old body", "userId": 1})
        post_id = create_resp.json()["id"]
        allure.attach(f"创建文章ID: {post_id}", "前置数据")
    
    with allure.step("Step1: 调用接口修改文章"):
        json_body = {
            "title": "DB校验-更新标题",
            "body": "更新落库校验",
            "userId": 1
        }
        allure.attach(str(json_body), "请求参数", allure.attachment_type.JSON)
        resp = requests.put(f"{BASE_URL}/posts/{post_id}", json=json_body)
        allure.attach(resp.text, "接口响应", allure.attachment_type.JSON)
        assert resp.status_code == 200

    with allure.step("Step2: 查询数据库校验更新"):
        cursor = db_conn.cursor()
        cursor.execute("SELECT title, body FROM posts WHERE id = ?", (post_id,))
        row = cursor.fetchone()
        allure.attach(f"DB查询结果: title={row['title']}, body={row['body']}", "数据库记录")

    with allure.step("Step3: 断言接口与DB一致性"):
        assert row is not None
        assert row["title"] == json_body["title"]
        assert row["body"] == json_body["body"]