"""
Locust 性能测试脚本
使用方式: locust -f locustfile.py --host=http://127.0.0.1:5000
"""
from locust import HttpUser, task, between


class ApiUser(HttpUser):
    """模拟 API 用户"""
    wait_time = between(0.1, 0.5)  # 每个用户请求间隔 0.1-0.5 秒

    @task(3)
    def get_posts_list(self):
        """获取文章列表 - 权重 3"""
        self.client.get("/posts")

    @task(2)
    def get_post_detail(self):
        """获取单篇文章 - 权重 2"""
        self.client.get("/posts/1")

    @task(1)
    def create_post(self):
        """创建文章 - 权重 1"""
        self.client.post(
            "/posts",
            json={"title": "Locust性能测试", "body": "性能测试body", "userId": 1}
        )

    @task(1)
    def get_products_list(self):
        """获取商品列表 - 权重 1"""
        self.client.get("/products")

    @task(1)
    def get_orders_list(self):
        """获取订单列表 - 权重 1"""
        self.client.get("/orders")

    @task(1)
    def get_user(self):
        """获取用户信息 - 权重 1"""
        self.client.get("/users/1")

    def on_start(self):
        """模拟用户登录（每个用户启动时执行）"""
        # 如果需要登录 token，可以在这里获取
        pass