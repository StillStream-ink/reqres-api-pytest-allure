import pytest
import requests
import allure
from common.config_util import ENV_CONFIG
from common.mock_server import get_db, USE_MYSQL
import os

BASE_URL = ENV_CONFIG["base_url"]
TIMEOUT = ENV_CONFIG["timeout"]

# MySQL 连接配置（Docker 环境下从环境变量读取）
MYSQL_HOST = os.environ.get("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3307"))
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "Toward123456")
MYSQL_DB = os.environ.get("MYSQL_DB", "my_test_db")


@allure.feature("MySQL集成测试")
@allure.story("接口新增 + MySQL落库校验")
def test_mysql_create_post():
    """验证接口新增文章后，数据真实写入 MySQL"""
    json_body = {
        "title": "MySQL集成测试文章",
        "body": "验证Flask Mock数据同步到MySQL",
        "userId": 1
    }
    resp = requests.post(f"{BASE_URL}/posts", json=json_body, timeout=TIMEOUT)
    assert resp.status_code == 201
    post_id = resp.json()["id"]
    allure.attach(f"创建文章ID: {post_id}", "接口响应")

  # 直连数据库校验落库（自动适配 MySQL 或 SQLite）
    ph = "%s" if USE_MYSQL else "?"
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT title, body, userId FROM posts WHERE id = {ph}", (post_id,))
        result = cursor.fetchone()
        allure.attach(str(result), "数据库查询结果")
        assert result is not None, "数据库中未找到新创建的文章"
        assert result["title"] == json_body["title"]
        assert result["body"] == json_body["body"]
        assert result["userId"] == json_body["userId"]
    finally:
        conn.close()


@allure.feature("MySQL集成测试")
@allure.story("MySQL预置数据 + 接口查询一致性")
def test_mysql_preset_data():
    """验证 MySQL 预置数据能通过接口正确查询"""
    # 查询 MySQL 中的预置文章
    ph = "%s" if USE_MYSQL else "?"
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT id, title FROM posts WHERE id = {ph}", (1,))
        result = cursor.fetchone()
        assert result is not None
        preset_title = result["title"]
    finally:
        conn.close()

    # 通过接口查询同一篇文章
    resp = requests.get(f"{BASE_URL}/posts/1", timeout=TIMEOUT)
    assert resp.status_code == 200
    assert resp.json()["title"] == preset_title


@allure.feature("MySQL集成测试")
@allure.story("接口修改 + MySQL数据同步校验")
def test_mysql_update_post():
    """验证接口修改后，MySQL数据同步更新"""
    # 先创建文章
    create_resp = requests.post(
        f"{BASE_URL}/posts",
        json={"title": "旧标题", "body": "旧内容", "userId": 1},
        timeout=TIMEOUT
    )
    assert create_resp.status_code == 201
    post_id = create_resp.json()["id"]

    # 修改文章
    update_body = {"title": "MySQL更新后的标题", "body": "MySQL更新后的内容"}
    resp = requests.put(f"{BASE_URL}/posts/{post_id}", json=update_body, timeout=TIMEOUT)
    assert resp.status_code == 200

    # 校验数据库（自动适配 MySQL 或 SQLite）
    ph = "%s" if USE_MYSQL else "?"
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT title, body FROM posts WHERE id = {ph}", (post_id,))
        result = cursor.fetchone()
        assert result is not None, "数据库中未找到修改后的文章"
        assert result["title"] == update_body["title"]
        assert result["body"] == update_body["body"]
    finally:
        conn.close()