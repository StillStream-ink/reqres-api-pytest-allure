import requests
from tenacity import retry, stop_after_attempt, wait_fixed

@retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
def send_request(method, url, params=None, json_data=None, timeout=10):
    """
    封装统一发送http请求，增加超时、异常捕获、重试
    :param method: 请求方式 GET / POST / PUT / DELETE
    :param url: 接口地址
    :param params: get查询参数
    :param json_data: post/put的body数据
    :param timeout: 超时时间，默认10秒
    :return: response对象；发生网络异常返回None
    """
    try:
        resp = requests.request(
            method=method,
            url=url,
            params=params,
            json=json_data,
            timeout=timeout
        )
        return resp
    except Exception:
        return None
