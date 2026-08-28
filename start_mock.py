import time
import os

# Wait for MySQL to be ready
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
        print("MySQL is ready!")
        break
    except Exception as e:
        print(f"Waiting for MySQL... ({i+1}/{max_retry}): {e}")
        time.sleep(2)
else:
    raise RuntimeError("MySQL connection failed after 30 retries")

from common.mock_server import app, init_db
init_db()
app.run(host='0.0.0.0', port=5000, debug=False)