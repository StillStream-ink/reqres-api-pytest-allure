import requests
import pytest
from tenacity import retry, stop_after_attempt, wait_fixed
import logging

logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
def send_request(method, url, params=None, json_data=None, headers=None, timeout=15):
    default_headers = {
        "Content-Type": "application/json;charset=utf-8"
    }
    if headers and isinstance(headers, dict):
        default_headers.update(headers)

    request_info = {
        "method": method.upper(),
        "url": url,
        "headers": default_headers,
        "body": json_data
    }

    logger.info(f"📤 请求: {method.upper()} {url} | 参数: {json_data}")

    resp = requests.request(
        method=method.upper(),
        url=url,
        params=params,
        json=json_data,
        headers=default_headers,
        timeout=timeout
    )

    if resp.status_code >= 400:
        logger.error(f"📥 响应: {resp.status_code} | Body: {resp.text[:500]}")
    else:
        logger.info(f"📥 响应: {resp.status_code}")

    # 保存请求信息到当前运行的 item
    try:
        current_item = getattr(pytest, '_current_item', None)
        if current_item:
            current_item._last_request = request_info
            current_item._last_response = resp
    except Exception:
        pass

    return resp