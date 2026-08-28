from flask import Flask, request, jsonify
import os
import sys
import socket
import time
import platform
import subprocess

app = Flask(__name__)

USE_MYSQL = False  # 保持 False，使用 SQLite

# SQLite 路径
DB_PATH = "reqres.db"

# MySQL 配置（保留兼容，但 USE_MYSQL=False 时用不到）
DB_CONFIG = {
    "host": os.environ.get("MYSQL_HOST", "127.0.0.1"),
    "port": int(os.environ.get("MYSQL_PORT", "3307")),
    "user": os.environ.get("MYSQL_USER", "root"),
    "password": os.environ.get("MYSQL_PASSWORD", "Toward123456"),
    "database": os.environ.get("MYSQL_DB", "my_test_db"),
    "charset": "utf8mb4",
}

if USE_MYSQL:
    import pymysql
    from pymysql.cursors import DictCursor

    def get_db():
        conn = pymysql.connect(**DB_CONFIG, cursorclass=DictCursor)
        return conn
else:
    import sqlite3
    DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'test_mock.db')

    def get_db():
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn


def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex(('127.0.0.1', port)) == 0


def kill_port(port):
    system = platform.system()
    try:
        if system == "Windows":
            result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
            for line in result.stdout.splitlines():
                if f":{port}" in line and "LISTENING" in line:
                    parts = line.strip().split()
                    pid = parts[-1]
                    if pid and pid.isdigit() and int(pid) > 0:
                        print(f"⚠️ 端口 {port} 被进程 PID={pid} 占用，正在释放...")
                        subprocess.run(['taskkill', '/F', '/PID', pid], capture_output=True)
                        return True
        else:
            result = subprocess.run(['lsof', '-ti', f':{port}'], capture_output=True, text=True)
            pids = result.stdout.strip()
            if pids:
                for pid in pids.splitlines():
                    pid = pid.strip()
                    if pid.isdigit():
                        print(f"⚠️ 端口 {port} 被进程 PID={pid} 占用，正在释放...")
                        os.kill(int(pid), 9)
                return True
    except Exception as e:
        print(f"⚠️ 清理端口异常: {e}")
    return False


def init_db():
    conn = get_db()
    c = conn.cursor()

    if USE_MYSQL:
        # MySQL 分支（保留，但当前不会执行）
        c.execute("DROP TABLE IF EXISTS posts")
        c.execute("DROP TABLE IF EXISTS users")
        c.execute("DROP TABLE IF EXISTS products")
        c.execute("DROP TABLE IF EXISTS orders")
        c.execute("DROP TABLE IF EXISTS comments")
        pass
    else:
        # ========== SQLite 分支 ==========
        # 1. 文章表
        c.execute("DROP TABLE IF EXISTS posts")
        c.execute("""
            CREATE TABLE posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                body TEXT,
                userId INTEGER
            )
        """)
        # 2. 用户表
        c.execute("DROP TABLE IF EXISTS users")
        c.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name TEXT,
                username TEXT,
                email TEXT
            )
        """)
        # 3. 商品表
        c.execute("DROP TABLE IF EXISTS products")
        c.execute("""
            CREATE TABLE products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL
            )
        """)
        # 4. 订单表
        c.execute("DROP TABLE IF EXISTS orders")
        c.execute("""
            CREATE TABLE orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                product_id INTEGER,
                quantity INTEGER,
                status TEXT
            )
        """)
        # 5. 🆕 评论表
        c.execute("DROP TABLE IF EXISTS comments")
        c.execute("""
            CREATE TABLE comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER,
                content TEXT,
                user_id INTEGER DEFAULT 1
            )
        """)

        # 预置数据：文章
        preset_posts = [
            (1, "preset_post_1", "Mock_data_1", 1),
            (2, "preset_post_2", "Mock_data_2", 1),
            (3, "preset_post_3", "Mock_data_3", 1),
            (4, "preset_post_4", "Mock_data_4", 1),
        ]
        c.executemany("INSERT INTO posts (id, title, body, userId) VALUES (?, ?, ?, ?)", preset_posts)

        # 预置数据：用户
        preset_users = [
            (1, "ZhangSan", "zhangsan", "zhangsan@test.com"),
            (2, "LiSi", "lisi", "lisi@test.com"),
        ]
        c.executemany("INSERT INTO users (id, name, username, email) VALUES (?, ?, ?, ?)", preset_users)

        # 预置数据：商品
        preset_products = [
            (1, "智能手表", 299.00),
            (2, "无线耳机", 89.00),
        ]
        c.executemany("INSERT INTO products (id, name, price) VALUES (?, ?, ?)", preset_products)

        # 预置数据：订单
        preset_orders = [
            (1, 1, 1, 2, 'pending'),
            (2, 2, 2, 1, 'shipped'),
        ]
        c.executemany("INSERT INTO orders (id, user_id, product_id, quantity, status) VALUES (?, ?, ?, ?, ?)", preset_orders)

        # 🆕 预置数据：评论
        preset_comments = [
            (1, 1, "这是一条测试评论1", 1),
            (2, 1, "这是一条测试评论2", 1),
        ]
        c.executemany("INSERT INTO comments (id, post_id, content, user_id) VALUES (?, ?, ?, ?)", preset_comments)

    conn.commit()
    conn.close()


# ==================== 文章模块 API ====================
@app.route('/posts', methods=['GET'])
def get_posts():
    conn = get_db()
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM posts")
        rows = c.fetchall()
        return jsonify([dict(row) for row in rows])
    finally:
        conn.close()


@app.route('/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    conn = get_db()
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
        row = c.fetchone()
        if row:
            return jsonify(dict(row))
        return jsonify({"error": "Not found"}), 404
    finally:
        conn.close()


@app.route('/posts', methods=['POST'])
def create_post():
    data = request.get_json() or {}
    conn = get_db()
    try:
        c = conn.cursor()
        c.execute("INSERT INTO posts (title, body, userId) VALUES (?, ?, ?)",
                  (data.get('title'), data.get('body'), data.get('userId', 1)))
        conn.commit()
        new_id = c.lastrowid
        return jsonify({
            "id": new_id,
            "title": data.get('title'),
            "body": data.get('body'),
            "userId": data.get('userId', 1)
        }), 201
    finally:
        conn.close()


@app.route('/posts/<int:post_id>', methods=['PUT'])
def update_post(post_id):
    data = request.get_json() or {}
    conn = get_db()
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
        if not c.fetchone():
            return jsonify({"error": "Not found"}), 404

        c.execute("SELECT title, body, userId FROM posts WHERE id = ?", (post_id,))
        old = c.fetchone()
        new_title = data.get('title', old['title'])
        new_body = data.get('body', old['body'])
        new_userId = data.get('userId', old['userId'])

        c.execute("UPDATE posts SET title=?, body=?, userId=? WHERE id=?",
                  (new_title, new_body, new_userId, post_id))
        conn.commit()

        c.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
        row = c.fetchone()
        return jsonify(dict(row))
    finally:
        conn.close()


@app.route('/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    conn = get_db()
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
        if not c.fetchone():
            return jsonify({"error": "Not found"}), 404
        c.execute("DELETE FROM posts WHERE id = ?", (post_id,))
        conn.commit()
        return jsonify({"message": "Deleted"}), 200
    finally:
        conn.close()


# ==================== 用户模块 API ====================
@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    conn = get_db()
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = c.fetchone()
        if row:
            return jsonify(dict(row))
        return jsonify({"error": "Not found"}), 404
    finally:
        conn.close()


@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json() or {}
    conn = get_db()
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        if not c.fetchone():
            return jsonify({"error": "Not found"}), 404

        c.execute("SELECT name, username, email FROM users WHERE id = ?", (user_id,))
        old = c.fetchone()
        new_name = data.get('name', old['name'])
        new_username = data.get('username', old['username'])
        new_email = data.get('email', old['email'])

        c.execute("UPDATE users SET name=?, username=?, email=? WHERE id=?",
                  (new_name, new_username, new_email, user_id))
        conn.commit()

        c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = c.fetchone()
        return jsonify(dict(row))
    finally:
        conn.close()


# ==================== 商品模块 API（完整 CRUD） ====================
@app.route('/products', methods=['GET'])
def get_products():
    conn = get_db()
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM products")
        rows = c.fetchall()
        return jsonify([dict(row) for row in rows])
    finally:
        conn.close()


@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    conn = get_db()
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        row = c.fetchone()
        if row:
            return jsonify(dict(row))
        return jsonify({"error": "Not found"}), 404
    finally:
        conn.close()


@app.route('/products', methods=['POST'])
def create_product():
    data = request.get_json() or {}
    conn = get_db()
    try:
        c = conn.cursor()
        c.execute("INSERT INTO products (name, price) VALUES (?, ?)",
                  (data.get('name'), data.get('price')))
        conn.commit()
        new_id = c.lastrowid
        return jsonify({
            "id": new_id,
            "name": data.get('name'),
            "price": data.get('price')
        }), 201
    finally:
        conn.close()


@app.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    data = request.get_json() or {}
    conn = get_db()
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        if not c.fetchone():
            return jsonify({"error": "Not found"}), 404

        c.execute("SELECT name, price FROM products WHERE id = ?", (product_id,))
        old = c.fetchone()
        new_name = data.get('name', old['name'])
        new_price = data.get('price', old['price'])

        c.execute("UPDATE products SET name=?, price=? WHERE id=?",
                  (new_name, new_price, product_id))
        conn.commit()

        c.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        row = c.fetchone()
        return jsonify(dict(row))
    finally:
        conn.close()


@app.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    conn = get_db()
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        if not c.fetchone():
            return jsonify({"error": "Not found"}), 404
        c.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()
        return jsonify({"message": "Deleted"}), 200
    finally:
        conn.close()


# ==================== 订单模块 API（完整 CRUD） ====================
@app.route('/orders', methods=['GET'])
def get_orders():
    conn = get_db()
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM orders")
        rows = c.fetchall()
        return jsonify([dict(row) for row in rows])
    finally:
        conn.close()


@app.route('/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    conn = get_db()
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        row = c.fetchone()
        if row:
            return jsonify(dict(row))
        return jsonify({"error": "Not found"}), 404
    finally:
        conn.close()


@app.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json() or {}
    conn = get_db()
    try:
        c = conn.cursor()
        c.execute("INSERT INTO orders (user_id, product_id, quantity, status) VALUES (?, ?, ?, ?)",
                  (data.get('user_id'), data.get('product_id'), data.get('quantity'), data.get('status', 'pending')))
        conn.commit()
        new_id = c.lastrowid
        return jsonify({
            "id": new_id,
            "user_id": data.get('user_id'),
            "product_id": data.get('product_id'),
            "quantity": data.get('quantity'),
            "status": data.get('status', 'pending')
        }), 201
    finally:
        conn.close()


@app.route('/orders/<int:order_id>', methods=['PUT'])
def update_order(order_id):
    data = request.get_json() or {}
    conn = get_db()
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        if not c.fetchone():
            return jsonify({"error": "Not found"}), 404

        c.execute("SELECT user_id, product_id, quantity, status FROM orders WHERE id = ?", (order_id,))
        old = c.fetchone()
        new_user_id = data.get('user_id', old['user_id'])
        new_product_id = data.get('product_id', old['product_id'])
        new_quantity = data.get('quantity', old['quantity'])
        new_status = data.get('status', old['status'])

        c.execute("UPDATE orders SET user_id=?, product_id=?, quantity=?, status=? WHERE id=?",
                  (new_user_id, new_product_id, new_quantity, new_status, order_id))
        conn.commit()

        c.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        row = c.fetchone()
        return jsonify(dict(row))
    finally:
        conn.close()


@app.route('/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    conn = get_db()
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        if not c.fetchone():
            return jsonify({"error": "Not found"}), 404
        c.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        conn.commit()
        return jsonify({"message": "Deleted"}), 200
    finally:
        conn.close()

# ==================== 评论模块 API（完整 CRUD） ====================
@app.route('/comments', methods=['GET'])
def get_comments():
    conn = get_db()
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM comments")
        rows = c.fetchall()
        return jsonify([dict(row) for row in rows])
    finally:
        conn.close()


@app.route('/comments/<int:comment_id>', methods=['GET'])
def get_comment(comment_id):
    conn = get_db()
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM comments WHERE id = ?", (comment_id,))
        row = c.fetchone()
        if row:
            return jsonify(dict(row))
        return jsonify({"error": "Not found"}), 404
    finally:
        conn.close()


@app.route('/comments', methods=['POST'])
def create_comment():
    data = request.get_json() or {}
    conn = get_db()
    try:
        c = conn.cursor()
        c.execute("INSERT INTO comments (post_id, content, user_id) VALUES (?, ?, ?)",
                  (data.get('post_id'), data.get('content'), data.get('user_id', 1)))
        conn.commit()
        new_id = c.lastrowid
        return jsonify({
            "id": new_id,
            "post_id": data.get('post_id'),
            "content": data.get('content'),
            "user_id": data.get('user_id', 1)
        }), 201
    finally:
        conn.close()


@app.route('/comments/<int:comment_id>', methods=['PUT'])
def update_comment(comment_id):
    data = request.get_json() or {}
    conn = get_db()
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM comments WHERE id = ?", (comment_id,))
        if not c.fetchone():
            return jsonify({"error": "Not found"}), 404

        c.execute("SELECT post_id, content, user_id FROM comments WHERE id = ?", (comment_id,))
        old = c.fetchone()
        new_post_id = data.get('post_id', old['post_id'])
        new_content = data.get('content', old['content'])
        new_user_id = data.get('user_id', old['user_id'])

        c.execute("UPDATE comments SET post_id=?, content=?, user_id=? WHERE id=?",
                  (new_post_id, new_content, new_user_id, comment_id))
        conn.commit()

        c.execute("SELECT * FROM comments WHERE id = ?", (comment_id,))
        row = c.fetchone()
        return jsonify(dict(row))
    finally:
        conn.close()


@app.route('/comments/<int:comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    conn = get_db()
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM comments WHERE id = ?", (comment_id,))
        if not c.fetchone():
            return jsonify({"error": "Not found"}), 404
        c.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
        conn.commit()
        return jsonify({"message": "Deleted"}), 200
    finally:
        conn.close()

if __name__ == '__main__':
    PORT = 5000
    if is_port_in_use(PORT):
        print(f"🔍 检测到端口 {PORT} 被占用，尝试自动清理...")
        killed = kill_port(PORT)
        if killed:
            time.sleep(1)
            if is_port_in_use(PORT):
                print(f"❌ 端口 {PORT} 仍然被占用，请手动执行以下命令后重试：")
                if platform.system() == "Windows":
                    print(f"   netstat -ano | findstr :{PORT}")
                    print(f"   taskkill /F /PID <PID号>")
                else:
                    print(f"   lsof -i :{PORT}")
                    print(f"   kill -9 <PID号>")
                sys.exit(1)
            else:
                print(f"✅ 端口 {PORT} 已成功释放")
        else:
            print(f"⚠️ 未能自动清理端口 {PORT}，请手动执行")
            sys.exit(1)
    else:
        print(f"✅ 端口 {PORT} 可用")

    init_db()
    print(f"🚀 Mock Server 启动在 http://0.0.0.0:{PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False, threaded=True)

__all__ = ['app', 'init_db', 'get_db', 'USE_MYSQL']