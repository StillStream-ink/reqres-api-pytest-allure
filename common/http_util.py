"""
统一 HTTP 请求封装
- 集成 tenacity 自动重试（默认 2 次，间隔 1 秒）
- 统一请求头
- 请求/响应日志
"""
import requests
import logging
from tenacity import retry, stop_after_attempt, wait_fixed

logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(2), wait=wait_fixed(1), reraise=True)
def send_request(method, url, params=None, json_data=None, headers=None, timeout=15):
    """
    统一发送 HTTP 请求，带超时、日志和自动重试

    :param method: 请求方式 GET / POST / PUT / DELETE
    :param url: 接口地址
    :param params: GET 查询参数
    :param json_data: POST/PUT 的 JSON body
    :param headers: 自定义请求头（会合并到默认头）
    :param timeout: 超时时间（秒），默认 15
    :return: requests.Response 对象
    """
    # 合并默认请求头
    default_headers = {"Content-Type": "application/json;charset=utf-8"}
    if headers and isinstance(headers, dict):
        default_headers.update(headers)

    # 请求日志
    logger.info(f"📤 请求: {method.upper()} {url} | 参数: {json_data}")

    resp = requests.request(
        method=method.upper(),
        url=url,
        params=params,
        json=json_data,
        headers=default_headers,
        timeout=timeout
    )

    # 响应日志
    if resp.status_code >= 400:
        logger.error(f"📥 响应: {resp.status_code} | Body: {resp.text[:500]}")
    else:
        logger.info(f"📥 响应: {resp.status_code}")

    return resp