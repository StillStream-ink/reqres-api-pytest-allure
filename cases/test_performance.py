"""
性能测试（轻量级并发）
使用 Pytest + ThreadPoolExecutor 模拟并发请求
适合日常 CI 回归中快速验证性能
"""
import pytest
import requests
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from common.config_util import ENV_CONFIG
import allure

BASE_URL = ENV_CONFIG["base_url"]
TIMEOUT = ENV_CONFIG["timeout"]


class TestPerformance:
    """性能测试套件"""

    @allure.feature("性能测试")
    @allure.story("GET /posts - 并发压测")
    @pytest.mark.slow
    def test_posts_list_concurrent(self):
        """并发 50 用户，每个用户请求 10 次，共 500 次请求"""
        url = f"{BASE_URL}/posts"
        concurrency = 50
        total_requests = 500

        def make_request():
            start = time.time()
            try:
                resp = requests.get(url, timeout=TIMEOUT)
                elapsed = time.time() - start
                return {"status": resp.status_code, "elapsed": elapsed, "success": True}
            except Exception as e:
                return {"status": 0, "elapsed": 0, "success": False, "error": str(e)}

        with allure.step(f"🔨 并发 {concurrency} 个用户，共 {total_requests} 次请求"):
            start_time = time.time()
            results = []
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = [executor.submit(make_request) for _ in range(total_requests)]
                for future in as_completed(futures):
                    results.append(future.result())

            total_duration = time.time() - start_time

        # 统计结果
        successful = [r for r in results if r.get("success", False) and r["status"] == 200]
        failed = [r for r in results if not r.get("success", False) or r["status"] != 200]
        success_rate = len(successful) / len(results) * 100 if results else 0

        elapsed_times = [r["elapsed"] for r in successful if r.get("elapsed", 0) > 0]

        # 生成报告
        report = f"""
📊 性能测试报告
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 接口: {url}
⏱️  总耗时: {total_duration:.2f}s
📝 总请求数: {total_requests}
✅ 成功数: {len(successful)}
❌ 失败数: {len(failed)}
📈 成功率: {success_rate:.2f}%

⏱️  响应时间统计（仅成功请求）:
   - 平均: {statistics.mean(elapsed_times):.3f}s" if elapsed_times else "   - 无有效数据"
   - 最大: {max(elapsed_times):.3f}s" if elapsed_times else "   - 无有效数据"
   - 最小: {min(elapsed_times):.3f}s" if elapsed_times else "   - 无有效数据"
   - P95: {sorted(elapsed_times)[int(len(elapsed_times) * 0.95)]:.3f}s" if elapsed_times else "   - 无有效数据"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        allure.attach(report, name="性能报告", attachment_type=allure.attachment_type.TEXT)

        # 断言（阈值已放宽）
        assert success_rate >= 85, f"❌ 成功率 {success_rate:.2f}% < 85%"
        if elapsed_times:
            assert statistics.mean(elapsed_times) < 1.0, f"❌ 平均响应时间 {statistics.mean(elapsed_times):.3f}s > 1.0s"

    @allure.feature("性能测试")
    @allure.story("POST /posts - 并发压测")
    @pytest.mark.slow
    def test_posts_create_concurrent(self):
        """并发创建文章（20 并发，100 次请求）"""
        url = f"{BASE_URL}/posts"
        concurrency = 20
        total_requests = 100

        def make_request():
            start = time.time()
            try:
                resp = requests.post(
                    url,
                    json={"title": f"性能测试-{time.time()}", "body": "性能测试body", "userId": 1},
                    timeout=TIMEOUT
                )
                elapsed = time.time() - start
                return {"status": resp.status_code, "elapsed": elapsed, "success": True}
            except Exception as e:
                return {"status": 0, "elapsed": 0, "success": False, "error": str(e)}

        with allure.step(f"🔨 并发 {concurrency} 个用户，共 {total_requests} 次创建"):
            start_time = time.time()
            results = []
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = [executor.submit(make_request) for _ in range(total_requests)]
                for future in as_completed(futures):
                    results.append(future.result())
            total_duration = time.time() - start_time

        successful = [r for r in results if r.get("success", False) and r["status"] == 201]
        failed = [r for r in results if not r.get("success", False) or r["status"] != 201]
        success_rate = len(successful) / len(results) * 100 if results else 0

        elapsed_times = [r["elapsed"] for r in successful if r.get("elapsed", 0) > 0]

        report = f"""
📊 性能测试报告（POST /posts）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 接口: {url}
⏱️  总耗时: {total_duration:.2f}s
📝 总请求数: {total_requests}
✅ 成功数: {len(successful)}
❌ 失败数: {len(failed)}
📈 成功率: {success_rate:.2f}%

⏱️  响应时间统计:
   - 平均: {statistics.mean(elapsed_times):.3f}s" if elapsed_times else "   - 无有效数据"
   - 最大: {max(elapsed_times):.3f}s" if elapsed_times else "   - 无有效数据"
   - 最小: {min(elapsed_times):.3f}s" if elapsed_times else "   - 无有效数据"
   - P95: {sorted(elapsed_times)[int(len(elapsed_times) * 0.95)]:.3f}s" if elapsed_times else "   - 无有效数据"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        allure.attach(report, name="性能报告", attachment_type=allure.attachment_type.TEXT)

        # 断言（阈值已放宽）
        assert success_rate >= 85, f"❌ 成功率 {success_rate:.2f}% < 85%"
        if elapsed_times:
            assert statistics.mean(elapsed_times) < 1.0, f"❌ 平均响应时间 {statistics.mean(elapsed_times):.3f}s > 1.0s"

    @allure.feature("性能测试")
    @allure.story("GET /posts/{id} - 参数化压测")
    @pytest.mark.parametrize("concurrency", [10, 30, 50])
    @pytest.mark.slow
    def test_posts_detail_concurrent(self, concurrency):
        """不同并发级别的单篇文章查询压测"""
        url = f"{BASE_URL}/posts/1"
        total_requests = concurrency * 5

        def make_request():
            start = time.time()
            try:
                resp = requests.get(url, timeout=TIMEOUT)
                elapsed = time.time() - start
                return {"status": resp.status_code, "elapsed": elapsed, "success": True}
            except Exception as e:
                return {"status": 0, "elapsed": 0, "success": False, "error": str(e)}

        with allure.step(f"🔨 并发 {concurrency} 个用户，共 {total_requests} 次请求"):
            start_time = time.time()
            results = []
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = [executor.submit(make_request) for _ in range(total_requests)]
                for future in as_completed(futures):
                    results.append(future.result())
            total_duration = time.time() - start_time

        successful = [r for r in results if r.get("success", False) and r["status"] == 200]
        success_rate = len(successful) / len(results) * 100 if results else 0
        elapsed_times = [r["elapsed"] for r in successful if r.get("elapsed", 0) > 0]

        allure.attach(
            f"并发: {concurrency} | 成功率: {success_rate:.2f}% | 平均响应: {statistics.mean(elapsed_times):.3f}s" if elapsed_times else f"并发: {concurrency} | 成功率: {success_rate:.2f}%",
            name=f"结果: concurrency={concurrency}",
            attachment_type=allure.attachment_type.TEXT
        )

        # 断言（阈值已放宽，与其他压测保持一致）
        assert success_rate >= 85, f"❌ 并发 {concurrency} 成功率 {success_rate:.2f}% < 85%"