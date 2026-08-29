import time
import os
import sys

# 检测是否在 Docker 环境
IS_DOCKER = os.environ.get("DOCKER_ENV", "false").lower() == "true"

if IS_DOCKER:
    # Docker 模式：等待 MySQL 就绪
    print("🐳 Docker 模式：等待 MySQL...")
    max_retry = 30
    for i in range(max_retry):
        try:
            import pymysql
            conn = pymysql.connect(
                host=os.environ.get("MYSQL_HOST", "mysql"),
                port=int(os.environ.get("MYSQL_PORT", "3306")),
                user=os.environ.get("MYSQL_USER", "testuser"),
                password=os.environ.get("MYSQL_PASSWORD", "testpass"),
                database=os.environ.get("MYSQL_DB", "reqres_test"),
                charset="utf8mb4",
                connect_timeout=5
            )
            conn.close()
            print("✅ MySQL is ready!")
            break
        except Exception as e:
            print(f"⏳ 等待 MySQL... ({i+1}/{max_retry}): {e}")
            time.sleep(2)
    else:
        raise RuntimeError("❌ MySQL connection failed after 30 retries")

# 启动 Mock 服务
from common.mock_server import app, init_db
init_db()
print("🚀 Mock Server 启动在 http://127.0.0.1:5000")
app.run(host='0.0.0.0' if IS_DOCKER else '127.0.0.1', port=5000, debug=False, use_reloader=False)