import pytest
import requests
import allure

BASE_URL = "https://jsonplaceholder.typicode.com"

# ---------------------- 公共封装函数（增加超时、异常捕获）----------------------
def send_request(method, url, params=None, json_data=None, timeout=10, retry=2):
    """带重试的请求封装"""
    for i in range(retry + 1):
        try:
            resp = requests.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                timeout=timeout
            )
            return resp
        except requests.exceptions.Timeout:
            print(f"\n【请求超时】第{i+1}次，url:{url}，超过{timeout}秒未响应")
        except requests.exceptions.ConnectionError:
            print(f"\n【网络连接失败】第{i+1}次，url:{url}")
        except Exception as e:
            print(f"\n【请求未知异常】url:{url}, 异常类型:{type(e)}, 异常信息：{str(e)}")
        import time
        time.sleep(1)
    # 全部重试失败才返回None
    return None


# ---------------------- 测试用例层 ----------------------
@allure.feature("文章模块")
@allure.story("获取文章列表")
def test_get_post_list():
    """GET 请求：获取文章列表"""
    url = f"{BASE_URL}/posts"
    resp = send_request(method="GET", url=url)

    assert resp is not None, "接口请求网络异常"
    print("\n【GET文章列表】", resp.json()[:2])
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "application/json" in resp.headers.get("Content-Type", "")
    assert data[0]["id"] == 1
    assert "title" in data[0]


@allure.feature("文章模块")
@allure.story("获取单篇文章")
def test_get_single_post():
    """GET 请求：获取单篇文章id=1"""
    url = f"{BASE_URL}/posts/1"
    resp = send_request("GET", url=url)

    assert resp is not None, "接口请求网络异常"
    print("\n【GET单篇文章】", resp.json())
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == 1
    assert "title" in body
    assert "body" in body
    assert isinstance(body["userId"], int)
    assert "application/json" in resp.headers.get("Content-Type", "")


@allure.feature("文章模块")
@allure.story("新增文章")
def test_post_create():
    """POST 请求：新增一篇文章"""
    url = f"{BASE_URL}/posts"
    payload = {
        "title": "软件测试学习笔记",
        "body": "pytest+requests接口自动化练习",
        "userId": 1
    }
    resp = send_request("POST", url=url, json_data=payload)

    assert resp is not None, "接口请求网络异常"
    print("\n【POST新增】", resp.json())
    assert resp.status_code == 201
    res_data = resp.json()
    assert res_data["title"] == "软件测试学习笔记"
    assert res_data["userId"] == 1
    assert "id" in res_data
    assert "application/json" in resp.headers.get("Content-Type", "")


@allure.feature("文章模块")
@allure.story("修改文章")
def test_put_update():
    """PUT 请求：完整更新id=1文章"""
    url = f"{BASE_URL}/posts/1"
    payload = {
        "title": "修改后的标题",
        "body": "修改后的正文内容",
        "userId": 1
    }
    resp = send_request("PUT", url=url, json_data=payload)

    assert resp is not None, "接口请求网络异常"
    print("\n【PUT更新】", resp.json())
    assert resp.status_code == 200
    assert resp.json()["title"] == "修改后的标题"
    assert resp.json()["userId"] == 1
    assert "application/json" in resp.headers.get("Content-Type", "")


@allure.feature("文章模块")
@allure.story("删除文章")
def test_delete_post():
    """DELETE 请求：删除id=1文章，二次校验"""
    url = f"{BASE_URL}/posts/1"
    resp = send_request("DELETE", url=url)
    assert resp is not None, "接口请求网络异常"
    assert resp.status_code == 200

    # 再次查询已删除资源（jsonplaceholder模拟接口仍能查到，仅演示真实业务思路）
    resp_check = send_request("GET", url=url)
    assert resp_check is not None



@allure.feature("文章模块")
@allure.story("参数化查询文章")
@pytest.mark.parametrize("post_id", [1, 2, 3, 4])
def test_get_post_param(post_id):
    """参数化：传入不同文章id获取数据"""
    url = f"{BASE_URL}/posts/{post_id}"
    resp = send_request("GET", url=url)

    assert resp is not None, "接口请求网络异常"
    print(f"\n查询文章id={post_id}", resp.json())
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == post_id
    assert isinstance(body["title"], str)
    assert "application/json" in resp.headers.get("Content-Type", "")


# 调试delete接口
if __name__ == "__main__":
    import requests
    BASE_URL = "https://reqres.in"
    url = f"{BASE_URL}/posts/1"
    res = requests.delete(url, timeout=10)
    print("status_code:", res.status_code)
    print("text:", repr(res.text))

