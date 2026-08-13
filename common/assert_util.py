"""
通用断言工具类，接口测试统一断言封装
"""
def assert_http_response(resp, expect_code=200):
    """
    基础响应断言：不为空 + 状态码校验
    :param resp: requests返回的response对象
    :param expect_code: 预期状态码，默认200
    """
    assert resp is not None, "❌ 请求返回为空，网络异常"
    assert resp.status_code == expect_code, f"❌ 状态码不一致！预期:{expect_code}，实际:{resp.status_code}"


def assert_json_key_exists(json_body, key):
    """校验json里指定key存在"""
    assert key in json_body, f"❌ 返回json缺少字段【{key}】"


def assert_json_value_equal(json_body, key, expect_val):
    """校验json指定key的值等于预期"""
    assert_json_key_exists(json_body, key)
    assert json_body[key] == expect_val, f"❌ 字段【{key}】值不一致！预期:{expect_val}，实际:{json_body[key]}"


def assert_json_type(json_body, key, expect_type):
    """校验json指定key的类型"""
    assert_json_key_exists(json_body, key)
    assert isinstance(json_body[key], expect_type), f"❌ 字段【{key}】类型不符！预期:{expect_type}，实际:{type(json_body[key])}"
