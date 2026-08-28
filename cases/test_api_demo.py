import pytest
import os
import sqlite3
import pymysql
from common.yaml_util import read_yaml
from common.log_util import logger
from common.config_util import ENV_CONFIG
from common.mock_server import get_db, USE_MYSQL
from common.http_util import send_request
from common.db_checker import check_and_assert
import allure
from config.schemas import (
    posts_list_schema,
    post_detail_schema,
    post_create_schema,
    products_list_schema,
    product_detail_schema,
    product_create_schema,
    orders_list_schema,
    order_detail_schema,
    order_create_schema,
    comments_list_schema,
    comment_detail_schema,
    comment_create_schema,
    user_schema
)
from common.schema_util import validate_with_step

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
    resp = send_request("POST", f"{BASE_URL}/posts", json_data=json_body, timeout=TIMEOUT)
    assert resp.status_code == 201
    res_json = resp.json()
    post_id = res_json["id"]
    yield post_id
    try:
        send_request("DELETE", f"{BASE_URL}/posts/{post_id}", timeout=TIMEOUT)
        logger.info(f"==== Fixture清理：删除文章 {post_id} ====")
    except Exception as e:
        logger.warning(f"清理文章 {post_id} 失败: {e}")


@allure.suite("文章模块")
class TestPostAPI:
    """文章相关接口测试"""

    @allure.feature("文章模块")
    @allure.story("获取文章列表")
    @pytest.mark.smoke
    def test_get_post_list(self):
        with allure.step("发送GET请求获取文章列表"):
            resp = send_request("GET", f"{BASE_URL}/posts", timeout=TIMEOUT)
            allure.attach(resp.text, "响应结果", allure.attachment_type.JSON)

        with allure.step("断言校验"):
            assert resp.status_code == 200
            data = resp.json()
            assert isinstance(data, list)
            assert len(data) >= 2

        # 🆕 JSON Schema 校验
        validate_with_step(data, posts_list_schema, "文章列表")

    @allure.feature("文章模块")
    @allure.story("获取单篇文章")
    @pytest.mark.smoke
    def test_get_single_post(self, new_post_id):
        with allure.step(f"发送GET请求查询文章ID={new_post_id}"):
            resp = send_request("GET", f"{BASE_URL}/posts/{new_post_id}", timeout=TIMEOUT)
            allure.attach(resp.text, "响应结果", allure.attachment_type.JSON)

        with allure.step("断言校验"):
            assert resp.status_code == 200
            data = resp.json()
            assert data["id"] == new_post_id

        # 🆕 JSON Schema 校验
        validate_with_step(data, post_detail_schema, "单篇文章")

    @allure.feature("文章模块")
    @allure.story("参数化查询文章")
    @pytest.mark.parametrize("post_id", [1, 2])
    def test_get_post_param(self, post_id):
        with allure.step(f"发送GET请求查询文章ID={post_id}"):
            resp = send_request("GET", f"{BASE_URL}/posts/{post_id}", timeout=TIMEOUT)
            allure.attach(resp.text, "响应结果", allure.attachment_type.JSON)

        with allure.step("断言校验"):
            assert resp.status_code == 200
            data = resp.json()
            assert data["id"] == post_id

        # 🆕 JSON Schema 校验
        validate_with_step(data, post_detail_schema, f"单篇文章ID={post_id}")

    @allure.feature("文章模块")
    @allure.story("新增文章")
    @pytest.mark.smoke
    def test_create_post(self):
        with allure.step("构造请求参数"):
            json_body = {
                "title": "测试自动化新增文章",
                "body": "接口自动化测试内容",
                "userId": 1
            }
            allure.attach(str(json_body), "请求参数", allure.attachment_type.JSON)

        with allure.step("发送POST请求"):
            resp = send_request("POST", f"{BASE_URL}/posts", json_data=json_body, timeout=TIMEOUT)
            allure.attach(resp.text, "响应结果", allure.attachment_type.JSON)

        with allure.step("断言校验"):
            assert resp.status_code == 201
            data = resp.json()
            assert data["title"] == json_body["title"]
            assert "id" in data

        # 🆕 JSON Schema 校验
        validate_with_step(data, post_create_schema, "创建文章")

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
            resp = send_request("PUT", f"{BASE_URL}/posts/{new_post_id}", json_data=json_body, timeout=TIMEOUT)
            allure.attach(resp.text, "响应结果", allure.attachment_type.JSON)

        with allure.step("断言校验"):
            assert resp.status_code == 200
            data = resp.json()
            assert data["title"] == json_body["title"]

        # 🆕 JSON Schema 校验
        validate_with_step(data, post_detail_schema, "修改文章")

    @allure.feature("文章模块")
    @allure.story("删除文章")
    def test_delete_post(self):
        with allure.step("前置：创建待删除文章"):
            payload = {"title": "to be deleted", "body": "delete me", "userId": 1}
            create_resp = send_request("POST", f"{BASE_URL}/posts", json_data=payload, timeout=TIMEOUT)
            post_id = create_resp.json()["id"]
            allure.attach(f"待删除文章ID: {post_id}", "前置数据")

        with allure.step(f"发送DELETE请求删除文章ID={post_id}"):
            resp = send_request("DELETE", f"{BASE_URL}/posts/{post_id}", timeout=TIMEOUT)
            allure.attach(f"状态码: {resp.status_code}", "删除响应")
            assert resp.status_code == 200

        with allure.step("验证文章已删除"):
            get_resp = send_request("GET", f"{BASE_URL}/posts/{post_id}", timeout=TIMEOUT)
            allure.attach(f"查询状态码: {get_resp.status_code}", "验证响应")
            assert get_resp.status_code == 404

    @allure.feature("文章模块")
    @allure.story("新增文章-接口+数据库校验")
    @pytest.mark.db
    def test_create_post_check_db(self):
        with allure.step("Step1: 调用接口新增文章"):
            json_body = {
                "title": "DB校验-新增文章",
                "body": "接口落库校验",
                "userId": 1
            }
            allure.attach(str(json_body), "请求参数", allure.attachment_type.JSON)
            resp = send_request("POST", f"{BASE_URL}/posts", json_data=json_body, timeout=TIMEOUT)
            allure.attach(resp.text, "接口响应", allure.attachment_type.JSON)
            assert resp.status_code == 201
            post_id = resp.json()["id"]
            allure.attach(f"新增文章ID: {post_id}", "提取ID")

        with allure.step("Step2: 查询数据库校验落库"):
            expected = {"title": json_body["title"], "body": json_body["body"]}
            check_and_assert("posts", post_id, expected)

        # 🆕 JSON Schema 校验
        validate_with_step(resp.json(), post_create_schema, "创建文章(DB双检)")

    @allure.feature("文章模块")
    @allure.story("修改文章-接口+数据库校验")
    @pytest.mark.db
    def test_update_post_check_db(self):
        with allure.step("前置：创建测试文章"):
            create_resp = send_request("POST", f"{BASE_URL}/posts",
                                        json_data={"title": "old title", "body": "old body", "userId": 1},
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
            resp = send_request("PUT", f"{BASE_URL}/posts/{post_id}", json_data=json_body, timeout=TIMEOUT)
            allure.attach(resp.text, "接口响应", allure.attachment_type.JSON)
            assert resp.status_code == 200

        with allure.step("Step2: 查询数据库校验更新"):
            expected = {"title": json_body["title"], "body": json_body["body"]}
            check_and_assert("posts", post_id, expected)

        # 🆕 JSON Schema 校验
        validate_with_step(resp.json(), post_detail_schema, "修改文章(DB双检)")

    # ==================== 商品模块 ====================
    @allure.feature("商品模块")
    @allure.story("获取商品列表")
    def test_get_products_list(self):
        with allure.step("发送GET请求获取商品列表"):
            resp = send_request("GET", f"{BASE_URL}/products", timeout=TIMEOUT)
            allure.attach(resp.text, "响应结果", allure.attachment_type.JSON)

        with allure.step("断言校验"):
            assert resp.status_code == 200
            data = resp.json()
            assert isinstance(data, list)
            assert len(data) >= 2

        # 🆕 JSON Schema 校验
        validate_with_step(data, products_list_schema, "商品列表")

    @allure.feature("商品模块")
    @allure.story("创建商品")
    def test_create_product(self):
        with allure.step("构造请求参数"):
            json_body = {"name": "测试机械键盘", "price": 199.00}
            allure.attach(str(json_body), "请求参数", allure.attachment_type.JSON)

        with allure.step("发送POST请求"):
            resp = send_request("POST", f"{BASE_URL}/products", json_data=json_body, timeout=TIMEOUT)
            allure.attach(resp.text, "响应结果", allure.attachment_type.JSON)

        with allure.step("断言校验"):
            assert resp.status_code == 201
            data = resp.json()
            assert data["name"] == json_body["name"]
            assert "id" in data

        # 🆕 JSON Schema 校验
        validate_with_step(data, product_create_schema, "创建商品")

    @allure.feature("商品模块")
    @allure.story("获取单个商品")
    def test_get_single_product(self):
        with allure.step("前置：创建测试商品"):
            create_resp = send_request("POST", f"{BASE_URL}/products",
                                        json_data={"name": "单测商品", "price": 66.66},
                                        timeout=TIMEOUT)
            assert create_resp.status_code == 201
            product_id = create_resp.json()["id"]
            allure.attach(f"创建商品ID: {product_id}", "前置数据")

        with allure.step(f"发送GET请求查询商品ID={product_id}"):
            resp = send_request("GET", f"{BASE_URL}/products/{product_id}", timeout=TIMEOUT)
            allure.attach(resp.text, "响应结果", allure.attachment_type.JSON)

        with allure.step("断言校验"):
            assert resp.status_code == 200
            data = resp.json()
            assert data["id"] == product_id
            assert data["name"] == "单测商品"

        # 🆕 JSON Schema 校验
        validate_with_step(data, product_detail_schema, "单个商品")

    @allure.feature("商品模块")
    @allure.story("修改商品")
    def test_update_product(self):
        with allure.step("前置：创建测试商品"):
            create_resp = send_request("POST", f"{BASE_URL}/products",
                                        json_data={"name": "旧商品", "price": 10.00},
                                        timeout=TIMEOUT)
            assert create_resp.status_code == 201
            product_id = create_resp.json()["id"]

        with allure.step("构造更新参数"):
            update_body = {"name": "新商品名", "price": 99.99}
            allure.attach(str(update_body), "请求参数", allure.attachment_type.JSON)

        with allure.step(f"发送PUT请求修改商品ID={product_id}"):
            resp = send_request("PUT", f"{BASE_URL}/products/{product_id}", json_data=update_body, timeout=TIMEOUT)
            allure.attach(resp.text, "响应结果", allure.attachment_type.JSON)

        with allure.step("断言校验"):
            assert resp.status_code == 200
            data = resp.json()
            assert data["name"] == update_body["name"]
            assert data["price"] == update_body["price"]

        # 🆕 JSON Schema 校验
        validate_with_step(data, product_detail_schema, "修改商品")

    @allure.feature("商品模块")
    @allure.story("删除商品")
    def test_delete_product(self):
        with allure.step("前置：创建待删除商品"):
            create_resp = send_request("POST", f"{BASE_URL}/products",
                                        json_data={"name": "待删除商品", "price": 1.00},
                                        timeout=TIMEOUT)
            assert create_resp.status_code == 201
            product_id = create_resp.json()["id"]
            allure.attach(f"待删除商品ID: {product_id}", "前置数据")

        with allure.step(f"发送DELETE请求删除商品ID={product_id}"):
            resp = send_request("DELETE", f"{BASE_URL}/products/{product_id}", timeout=TIMEOUT)
            allure.attach(f"状态码: {resp.status_code}", "删除响应")
            assert resp.status_code == 200

        with allure.step("验证商品已删除"):
            get_resp = send_request("GET", f"{BASE_URL}/products/{product_id}", timeout=TIMEOUT)
            allure.attach(f"查询状态码: {get_resp.status_code}", "验证响应")
            assert get_resp.status_code == 404

    @allure.feature("商品模块")
    @allure.story("新增商品-接口+数据库校验")
    @pytest.mark.db
    def test_create_product_check_db(self):
        with allure.step("Step1: 调用接口新增商品"):
            json_body = {
                "name": "DB双检-新增商品",
                "price": 299.99
            }
            allure.attach(str(json_body), "请求参数", allure.attachment_type.JSON)
            resp = send_request("POST", f"{BASE_URL}/products", json_data=json_body, timeout=TIMEOUT)
            allure.attach(resp.text, "接口响应", allure.attachment_type.JSON)
            assert resp.status_code == 201
            product_id = resp.json()["id"]
            allure.attach(f"新增商品ID: {product_id}", "提取ID")

        with allure.step("Step2: 查询数据库校验落库"):
            expected = {"name": json_body["name"], "price": json_body["price"]}
            check_and_assert("products", product_id, expected)

        # 🆕 JSON Schema 校验
        validate_with_step(resp.json(), product_create_schema, "创建商品(DB双检)")

    @allure.feature("商品模块")
    @allure.story("修改商品-接口+数据库校验")
    @pytest.mark.db
    def test_update_product_check_db(self):
        with allure.step("前置：创建测试商品"):
            create_resp = send_request("POST", f"{BASE_URL}/products",
                                        json_data={"name": "旧商品名", "price": 10.00},
                                        timeout=TIMEOUT)
            assert create_resp.status_code == 201
            product_id = create_resp.json()["id"]
            allure.attach(f"创建商品ID: {product_id}", "前置数据")

        with allure.step("Step1: 调用接口修改商品"):
            json_body = {
                "name": "DB双检-更新商品名",
                "price": 888.88
            }
            allure.attach(str(json_body), "请求参数", allure.attachment_type.JSON)
            resp = send_request("PUT", f"{BASE_URL}/products/{product_id}", json_data=json_body, timeout=TIMEOUT)
            allure.attach(resp.text, "接口响应", allure.attachment_type.JSON)
            assert resp.status_code == 200

        with allure.step("Step2: 查询数据库校验更新"):
            expected = {"name": json_body["name"], "price": json_body["price"]}
            check_and_assert("products", product_id, expected)

        # 🆕 JSON Schema 校验
        validate_with_step(resp.json(), product_detail_schema, "修改商品(DB双检)")

    # ==================== 订单模块 ====================
    @allure.feature("订单模块")
    @allure.story("获取订单列表")
    def test_get_orders_list(self):
        with allure.step("发送GET请求获取订单列表"):
            resp = send_request("GET", f"{BASE_URL}/orders", timeout=TIMEOUT)
            allure.attach(resp.text, "响应结果", allure.attachment_type.JSON)

        with allure.step("断言校验"):
            assert resp.status_code == 200
            data = resp.json()
            assert isinstance(data, list)
            assert len(data) >= 2

        # 🆕 JSON Schema 校验
        validate_with_step(data, orders_list_schema, "订单列表")

    @allure.feature("订单模块")
    @allure.story("创建订单")
    def test_create_order(self):
        with allure.step("构造请求参数"):
            json_body = {"user_id": 1, "product_id": 2, "quantity": 3, "status": "pending"}
            allure.attach(str(json_body), "请求参数", allure.attachment_type.JSON)

        with allure.step("发送POST请求"):
            resp = send_request("POST", f"{BASE_URL}/orders", json_data=json_body, timeout=TIMEOUT)
            allure.attach(resp.text, "响应结果", allure.attachment_type.JSON)

        with allure.step("断言校验"):
            assert resp.status_code == 201
            data = resp.json()
            assert data["user_id"] == json_body["user_id"]
            assert "id" in data

        # 🆕 JSON Schema 校验
        validate_with_step(data, order_create_schema, "创建订单")

    @allure.feature("订单模块")
    @allure.story("获取单个订单")
    def test_get_single_order(self):
        with allure.step("前置：创建测试订单"):
            create_resp = send_request("POST", f"{BASE_URL}/orders",
                                        json_data={"user_id": 1, "product_id": 1, "quantity": 2, "status": "pending"},
                                        timeout=TIMEOUT)
            assert create_resp.status_code == 201
            order_id = create_resp.json()["id"]

        with allure.step(f"发送GET请求查询订单ID={order_id}"):
            resp = send_request("GET", f"{BASE_URL}/orders/{order_id}", timeout=TIMEOUT)
            allure.attach(resp.text, "响应结果", allure.attachment_type.JSON)

        with allure.step("断言校验"):
            assert resp.status_code == 200
            data = resp.json()
            assert data["id"] == order_id

        # 🆕 JSON Schema 校验
        validate_with_step(data, order_detail_schema, "单个订单")

    @allure.feature("订单模块")
    @allure.story("修改订单")
    def test_update_order(self):
        with allure.step("前置：创建测试订单"):
            create_resp = send_request("POST", f"{BASE_URL}/orders",
                                        json_data={"user_id": 1, "product_id": 1, "quantity": 1, "status": "pending"},
                                        timeout=TIMEOUT)
            assert create_resp.status_code == 201
            order_id = create_resp.json()["id"]

        with allure.step("构造更新参数"):
            update_body = {"status": "shipped", "quantity": 99}

        with allure.step(f"发送PUT请求修改订单ID={order_id}"):
            resp = send_request("PUT", f"{BASE_URL}/orders/{order_id}", json_data=update_body, timeout=TIMEOUT)
            allure.attach(resp.text, "响应结果", allure.attachment_type.JSON)

        with allure.step("断言校验"):
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == update_body["status"]
            assert data["quantity"] == update_body["quantity"]

        # 🆕 JSON Schema 校验
        validate_with_step(data, order_detail_schema, "修改订单")

    @allure.feature("订单模块")
    @allure.story("删除订单")
    def test_delete_order(self):
        with allure.step("前置：创建待删除订单"):
            create_resp = send_request("POST", f"{BASE_URL}/orders",
                                        json_data={"user_id": 1, "product_id": 1, "quantity": 1, "status": "pending"},
                                        timeout=TIMEOUT)
            assert create_resp.status_code == 201
            order_id = create_resp.json()["id"]

        with allure.step(f"发送DELETE请求删除订单ID={order_id}"):
            resp = send_request("DELETE", f"{BASE_URL}/orders/{order_id}", timeout=TIMEOUT)
            assert resp.status_code == 200

        with allure.step("验证订单已删除"):
            get_resp = send_request("GET", f"{BASE_URL}/orders/{order_id}", timeout=TIMEOUT)
            assert get_resp.status_code == 404

    @allure.feature("订单模块")
    @allure.story("创建订单-接口+数据库校验")
    @pytest.mark.db
    def test_create_order_check_db(self):
        with allure.step("Step1: 调用接口新增订单"):
            json_body = {"user_id": 2, "product_id": 2, "quantity": 7, "status": "pending"}
            allure.attach(str(json_body), "请求参数", allure.attachment_type.JSON)
            resp = send_request("POST", f"{BASE_URL}/orders", json_data=json_body, timeout=TIMEOUT)
            allure.attach(resp.text, "接口响应", allure.attachment_type.JSON)
            assert resp.status_code == 201
            order_id = resp.json()["id"]
            allure.attach(f"新增订单ID: {order_id}", "提取ID")

        with allure.step("Step2: 查询数据库校验落库"):
            expected = {"user_id": json_body["user_id"], "quantity": json_body["quantity"], "status": json_body["status"]}
            check_and_assert("orders", order_id, expected)

        # 🆕 JSON Schema 校验
        validate_with_step(resp.json(), order_create_schema, "创建订单(DB双检)")

    @allure.feature("订单模块")
    @allure.story("修改订单-接口+数据库校验")
    @pytest.mark.db
    def test_update_order_check_db(self):
        with allure.step("前置：创建测试订单"):
            create_resp = send_request("POST", f"{BASE_URL}/orders",
                                        json_data={"user_id": 1, "product_id": 1, "quantity": 1, "status": "pending"},
                                        timeout=TIMEOUT)
            assert create_resp.status_code == 201
            order_id = create_resp.json()["id"]

        with allure.step("Step1: 调用接口修改订单"):
            json_body = {"quantity": 888, "status": "completed"}
            allure.attach(str(json_body), "请求参数", allure.attachment_type.JSON)
            resp = send_request("PUT", f"{BASE_URL}/orders/{order_id}", json_data=json_body, timeout=TIMEOUT)
            allure.attach(resp.text, "接口响应", allure.attachment_type.JSON)
            assert resp.status_code == 200

        with allure.step("Step2: 查询数据库校验更新"):
            expected = {"quantity": json_body["quantity"], "status": json_body["status"]}
            check_and_assert("orders", order_id, expected)

        # 🆕 JSON Schema 校验
        validate_with_step(resp.json(), order_detail_schema, "修改订单(DB双检)")

    # ==================== 评论模块 ====================
    @allure.feature("评论模块")
    @allure.story("获取评论列表")
    def test_get_comments_list(self):
        with allure.step("发送GET请求获取评论列表"):
            resp = send_request("GET", f"{BASE_URL}/comments", timeout=TIMEOUT)
            allure.attach(resp.text, "响应结果", allure.attachment_type.JSON)

        with allure.step("断言校验"):
            assert resp.status_code == 200
            data = resp.json()
            assert isinstance(data, list)
            assert len(data) >= 2

        # 🆕 JSON Schema 校验
        validate_with_step(data, comments_list_schema, "评论列表")

    @allure.feature("评论模块")
    @allure.story("创建评论")
    def test_create_comment(self):
        with allure.step("构造请求参数"):
            json_body = {"post_id": 1, "content": "自动化测试评论", "user_id": 1}
            allure.attach(str(json_body), "请求参数", allure.attachment_type.JSON)

        with allure.step("发送POST请求"):
            resp = send_request("POST", f"{BASE_URL}/comments", json_data=json_body, timeout=TIMEOUT)
            allure.attach(resp.text, "响应结果", allure.attachment_type.JSON)

        with allure.step("断言校验"):
            assert resp.status_code == 201
            data = resp.json()
            assert data["content"] == json_body["content"]
            assert "id" in data

        # 🆕 JSON Schema 校验
        validate_with_step(data, comment_create_schema, "创建评论")

    @allure.feature("评论模块")
    @allure.story("获取单个评论")
    def test_get_single_comment(self):
        with allure.step("前置：创建测试评论"):
            create_resp = send_request("POST", f"{BASE_URL}/comments",
                                        json_data={"post_id": 1, "content": "单测评论", "user_id": 1},
                                        timeout=TIMEOUT)
            assert create_resp.status_code == 201
            comment_id = create_resp.json()["id"]
            allure.attach(f"创建评论ID: {comment_id}", "前置数据")

        with allure.step(f"发送GET请求查询评论ID={comment_id}"):
            resp = send_request("GET", f"{BASE_URL}/comments/{comment_id}", timeout=TIMEOUT)
            allure.attach(resp.text, "响应结果", allure.attachment_type.JSON)

        with allure.step("断言校验"):
            assert resp.status_code == 200
            data = resp.json()
            assert data["id"] == comment_id
            assert data["content"] == "单测评论"

        # 🆕 JSON Schema 校验
        validate_with_step(data, comment_detail_schema, "单个评论")

    @allure.feature("评论模块")
    @allure.story("修改评论")
    def test_update_comment(self):
        with allure.step("前置：创建测试评论"):
            create_resp = send_request("POST", f"{BASE_URL}/comments",
                                        json_data={"post_id": 1, "content": "旧评论", "user_id": 1},
                                        timeout=TIMEOUT)
            assert create_resp.status_code == 201
            comment_id = create_resp.json()["id"]

        with allure.step("构造更新参数"):
            update_body = {"content": "更新后的评论"}
            allure.attach(str(update_body), "请求参数", allure.attachment_type.JSON)

        with allure.step(f"发送PUT请求修改评论ID={comment_id}"):
            resp = send_request("PUT", f"{BASE_URL}/comments/{comment_id}", json_data=update_body, timeout=TIMEOUT)
            allure.attach(resp.text, "响应结果", allure.attachment_type.JSON)

        with allure.step("断言校验"):
            assert resp.status_code == 200
            data = resp.json()
            assert data["content"] == update_body["content"]

        # 🆕 JSON Schema 校验
        validate_with_step(data, comment_detail_schema, "修改评论")

    @allure.feature("评论模块")
    @allure.story("删除评论")
    def test_delete_comment(self):
        with allure.step("前置：创建待删除评论"):
            create_resp = send_request("POST", f"{BASE_URL}/comments",
                                        json_data={"post_id": 1, "content": "待删除评论", "user_id": 1},
                                        timeout=TIMEOUT)
            assert create_resp.status_code == 201
            comment_id = create_resp.json()["id"]
            allure.attach(f"待删除评论ID: {comment_id}", "前置数据")

        with allure.step(f"发送DELETE请求删除评论ID={comment_id}"):
            resp = send_request("DELETE", f"{BASE_URL}/comments/{comment_id}", timeout=TIMEOUT)
            allure.attach(f"状态码: {resp.status_code}", "删除响应")
            assert resp.status_code == 200

        with allure.step("验证评论已删除"):
            get_resp = send_request("GET", f"{BASE_URL}/comments/{comment_id}", timeout=TIMEOUT)
            allure.attach(f"查询状态码: {get_resp.status_code}", "验证响应")
            assert get_resp.status_code == 404

    @allure.feature("评论模块")
    @allure.story("创建评论-接口+数据库校验")
    @pytest.mark.db
    def test_create_comment_check_db(self):
        with allure.step("Step1: 调用接口新增评论"):
            json_body = {"post_id": 1, "content": "DB双检-新增评论", "user_id": 1}
            allure.attach(str(json_body), "请求参数", allure.attachment_type.JSON)
            resp = send_request("POST", f"{BASE_URL}/comments", json_data=json_body, timeout=TIMEOUT)
            allure.attach(resp.text, "接口响应", allure.attachment_type.JSON)
            assert resp.status_code == 201
            comment_id = resp.json()["id"]
            allure.attach(f"新增评论ID: {comment_id}", "提取ID")

        with allure.step("Step2: 查询数据库校验落库"):
            expected = {"content": json_body["content"], "user_id": json_body["user_id"]}
            check_and_assert("comments", comment_id, expected)

        # 🆕 JSON Schema 校验
        validate_with_step(resp.json(), comment_create_schema, "创建评论(DB双检)")

    @allure.feature("评论模块")
    @allure.story("修改评论-接口+数据库校验")
    @pytest.mark.db
    def test_update_comment_check_db(self):
        with allure.step("前置：创建测试评论"):
            create_resp = send_request("POST", f"{BASE_URL}/comments",
                                        json_data={"post_id": 1, "content": "旧评论", "user_id": 1},
                                        timeout=TIMEOUT)
            assert create_resp.status_code == 201
            comment_id = create_resp.json()["id"]
            allure.attach(f"创建评论ID: {comment_id}", "前置数据")

        with allure.step("Step1: 调用接口修改评论"):
            json_body = {"content": "DB双检-更新评论"}
            allure.attach(str(json_body), "请求参数", allure.attachment_type.JSON)
            resp = send_request("PUT", f"{BASE_URL}/comments/{comment_id}", json_data=json_body, timeout=TIMEOUT)
            allure.attach(resp.text, "接口响应", allure.attachment_type.JSON)
            assert resp.status_code == 200

        with allure.step("Step2: 查询数据库校验更新"):
            expected = {"content": json_body["content"]}
            check_and_assert("comments", comment_id, expected)

        # 🆕 JSON Schema 校验
        validate_with_step(resp.json(), comment_detail_schema, "修改评论(DB双检)")