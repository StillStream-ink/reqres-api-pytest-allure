import pytest
import allure
import os
from common.yaml_util import read_yaml, replace_placeholder
from common.assert_util import *

BASE_URL = "https://jsonplaceholder.typicode.com"
base_path = os.path.dirname(os.path.abspath(__file__))
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

    from test_api_demo import send_request
    resp = send_request(method=method, url=full_url, json_data=json_data)
    assert_http_response(resp, expect_code)
    body = resp.json()

    # 执行校验规则
    check_rule = case_info.get("check", {})
    # 判断是否是列表
    if check_rule.get("is_list") is True:
        assert isinstance(body, list), "❌ 返回不是数组"
        if check_rule.get("has_keys") and len(body) > 0:
            for k in check_rule["has_keys"]:
                assert_json_key_exists(body[0], k)
    # 等值断言
    if check_rule.get("equal"):
        for k,v in check_rule["equal"].items():
            real_v = replace_placeholder(v, replace_data)
            # 修复点：先判断是不是字符串，再isdigit
            if isinstance(real_v, str) and real_v.isdigit():
                real_v = int(real_v)
            assert_json_value_equal(body, k, real_v)
    # 类型断言
    if check_rule.get("type"):
        type_map = {"str": str, "int": int}
        for k,t in check_rule["type"].items():
            assert_json_type(body, k, type_map[t])
    return resp

# -------------------- 逐个注册用例 --------------------
@allure.feature("文章模块")
@allure.story("获取文章列表")
def test_post_list():
    run_api_case(yaml_data["post_list"])

@allure.feature("文章模块")
@allure.story("获取单篇文章")
def test_post_single():
    run_api_case(yaml_data["post_single"])

@allure.feature("文章模块")
@allure.story("参数化查询文章")
@pytest.mark.parametrize("post_id", yaml_data["post_param"]["params_list"])
def test_post_param(post_id):
    run_api_case(yaml_data["post_param"], replace_data={"post_id":post_id})

@allure.feature("文章模块")
@allure.story("新增文章")
def test_post_create():
    run_api_case(yaml_data["post_create"])

@allure.feature("文章模块")
@allure.story("修改文章")
def test_post_update():
    run_api_case(yaml_data["post_update"])

@allure.feature("文章模块")
@allure.story("删除文章")
def test_post_delete():
    run_api_case(yaml_data["post_delete"])

@allure.feature("用户模块")
@allure.story("用户信息查询（带token鉴权）")
def test_user_info(user_token):
    run_api_case(yaml_data["user_info"])
    
# -------------------- 业务链路：文章全生命周期（串行依赖）--------------------
@allure.feature("文章模块")
@allure.story("文章完整业务链路：新增→查询→修改→删除")
@pytest.fixture(scope="class")
def flow_post_id():
    """直接使用服务自带存在的文章id=1（jsonplaceholder不会持久化新建数据）"""
    return 1


def test_flow_get(flow_post_id):
    run_api_case(yaml_data["post_flow_get"], replace_data={"flow_post_id": flow_post_id})

def test_flow_update(flow_post_id):
    run_api_case(yaml_data["post_flow_update"], replace_data={"flow_post_id": flow_post_id})

def test_flow_delete(flow_post_id):
    run_api_case(yaml_data["post_flow_delete"], replace_data={"flow_post_id": flow_post_id})
