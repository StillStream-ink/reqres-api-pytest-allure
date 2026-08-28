import pytest
import allure
import requests
import os
import copy
from common.yaml_util import read_yaml, replace_placeholder
from common.assert_util import *
from common.config_util import ENV_CONFIG
from config.schemas import (
    posts_list_schema,
    post_detail_schema,
    post_create_schema,
    user_schema
)
from common.schema_util import validate_with_step

BASE_URL = ENV_CONFIG["base_url"]
TIMEOUT = ENV_CONFIG["timeout"]
base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
yaml_data = read_yaml(os.path.join(base_path, "config/test_data.yaml"))

# 单独封装统一执行函数
def run_api_case(case_info, replace_data=None):
    if replace_data is None:
        replace_data = {}
    method = replace_placeholder(case_info["method"], replace_data)
    api_url = replace_placeholder(case_info["url"], replace_data)
    full_url = f"{BASE_URL}{api_url}"
    json_data = case_info.get("json")
    expect_code = case_info["expect_code"]

    resp = requests.request(method=method, url=full_url, json=json_data, timeout=TIMEOUT)
    assert_http_response(resp, expect_code)
    body = resp.json()

    # 执行校验规则
    check_rule = case_info.get("check", {})
    if check_rule.get("is_list") is True:
        assert isinstance(body, list), "❌ 返回不是数组"
        if check_rule.get("has_keys") and len(body) > 0:
            for k in check_rule["has_keys"]:
                assert_json_key_exists(body[0], k)
    if check_rule.get("equal"):
        for k,v in check_rule["equal"].items():
            real_v = replace_placeholder(v, replace_data)
            if isinstance(real_v, str) and real_v.isdigit():
                real_v = int(real_v)
            assert_json_value_equal(body, k, real_v)
    if check_rule.get("type"):
        type_map = {"str": str, "int": int}
        for k,t in check_rule["type"].items():
            assert_json_type(body, k, type_map[t])
    return resp

# -------------------- 逐个注册用例 --------------------
@allure.feature("文章模块")
@allure.story("获取文章列表")
def test_post_list():
    resp = run_api_case(yaml_data["post_list"])
    # 🆕 JSON Schema 校验
    validate_with_step(resp.json(), posts_list_schema, "文章列表(数据驱动)")

@allure.feature("文章模块")
@allure.story("获取单篇文章")
def test_post_single():
    resp = run_api_case(yaml_data["post_single"])
    # 🆕 JSON Schema 校验
    validate_with_step(resp.json(), post_detail_schema, "单篇文章(数据驱动)")

@allure.feature("文章模块")
@allure.story("参数化查询文章")
@pytest.mark.parametrize("post_id", yaml_data["post_param"]["params_list"])
def test_post_param(post_id):
    resp = run_api_case(yaml_data["post_param"], replace_data={"post_id":post_id})
    # 🆕 JSON Schema 校验
    validate_with_step(resp.json(), post_detail_schema, f"参数化查询文章ID={post_id}")

@allure.feature("文章模块")
@allure.story("新增文章")
def test_post_create():
    resp = run_api_case(yaml_data["post_create"])
    # 🆕 JSON Schema 校验
    validate_with_step(resp.json(), post_create_schema, "创建文章(数据驱动)")

@allure.feature("文章模块")
@allure.story("修改文章")
def test_post_update():
    resp = run_api_case(yaml_data["post_update"])
    # 🆕 JSON Schema 校验
    validate_with_step(resp.json(), post_detail_schema, "修改文章(数据驱动)")

@allure.feature("文章模块")
@allure.story("删除文章")
def test_post_delete():
    # 修复：先创建新文章，再删除新文章，避免删除预置数据
    create_resp = requests.post(
        f"{BASE_URL}/posts",
        json={"title": "删除测试文章", "body": "待删除", "userId": 1},
        timeout=TIMEOUT
    )
    assert create_resp.status_code == 201
    post_id = create_resp.json()["id"]

    case_info = copy.deepcopy(yaml_data["post_delete"])
    # 替换 url 中的 post_id
    case_info["url"] = case_info["url"].replace("1", str(post_id)).replace("{post_id}", str(post_id))
    run_api_case(case_info)

@allure.feature("用户模块")
@allure.story("用户信息查询（带token鉴权）")
def test_user_info(user_token):
    resp = run_api_case(yaml_data["user_info"])
    # 🆕 JSON Schema 校验
    validate_with_step(resp.json(), user_schema, "用户信息(数据驱动)")

# -------------------- 业务链路：文章全生命周期（串行依赖）--------------------
@pytest.fixture(scope="class")
def flow_post_id():
    """创建一篇新文章供链路测试使用，测试结束后自动清理"""
    resp = requests.post(
        f"{BASE_URL}/posts",
        json={"title": "链路测试文章", "body": "flow测试", "userId": 1},
        timeout=TIMEOUT
    )
    assert resp.status_code == 201
    post_id = resp.json()["id"]
    yield post_id
    try:
        requests.delete(f"{BASE_URL}/posts/{post_id}", timeout=TIMEOUT)
    except Exception:
        pass


@allure.feature("文章模块")
@allure.story("文章完整业务链路-查询")
def test_flow_get(flow_post_id):
    case_info = copy.deepcopy(yaml_data["post_flow_get"])
    if "check" in case_info and "equal" in case_info["check"]:
        case_info["check"]["equal"]["id"] = str(flow_post_id)
    resp = run_api_case(case_info, replace_data={"flow_post_id": flow_post_id})
    # 🆕 JSON Schema 校验
    validate_with_step(resp.json(), post_detail_schema, "链路查询文章")

@allure.feature("文章模块")
@allure.story("文章完整业务链路-修改")
def test_flow_update(flow_post_id):
    case_info = copy.deepcopy(yaml_data["post_flow_update"])
    if "check" in case_info and "equal" in case_info["check"]:
        case_info["check"]["equal"]["id"] = str(flow_post_id)
    resp = run_api_case(case_info, replace_data={"flow_post_id": flow_post_id})
    # 🆕 JSON Schema 校验
    validate_with_step(resp.json(), post_detail_schema, "链路修改文章")

@allure.feature("文章模块")
@allure.story("文章完整业务链路-删除")
def test_flow_delete(flow_post_id):
    case_info = copy.deepcopy(yaml_data["post_flow_delete"])
    if "check" in case_info and "equal" in case_info["check"]:
        case_info["check"]["equal"]["id"] = str(flow_post_id)
    run_api_case(case_info, replace_data={"flow_post_id": flow_post_id})