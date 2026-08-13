import requests
from tenacity import retry, stop_after_attempt, wait_fixed
import logging

logger = logging.getLogger(__name__)

@retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
def send_request(method, url, params=None, json_data=None, headers=None, timeout=15):
    """
    统一封装HTTP请求，网络异常自动重试2次
    """
    default_headers = {
        "Content-Type": "application/json;charset=utf-8"
    }
    if headers and isinstance(headers, dict):
        default_headers.update(headers)

    resp = requests.request(
        method=method.upper(),
        url=url,
        params=params,
        json=json_data,
        headers=default_headers,
        timeout=timeout
    )
    return resp
