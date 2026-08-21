from flask import Flask, request, jsonify
import os

app = Flask(__name__)

USE_MYSQL = True

# SQLite 路径（兼容旧代码导入）
DB_PATH = "reqres.db"

# ★ 新增：MySQL 连接配置字典（供测试文件导入使用）
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


def init_db():
    conn = get_db()
    c = conn.cursor()

    if USE_MYSQL:
        c.execute("DROP TABLE IF EXISTS posts")
        c.execute("DROP TABLE IF EXISTS users")
        c.execute("""
            CREATE TABLE posts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                body TEXT,
                userId INT DEFAULT 1
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        c.execute("""
            CREATE TABLE users (
                id INT PRIMARY KEY,
                name VARCHAR(100),
                username VARCHAR(100),
                email VARCHAR(100)
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        preset_posts = [
            (1, "preset_post_1", "Mock_data_1", 1),
            (2, "preset_post_2", "Mock_data_2", 1),
            (3, "preset_post_3", "Mock_data_3", 1),
            (4, "preset_post_4", "Mock_data_4", 1),
        ]
        c.executemany("INSERT INTO posts (id, title, body, userId) VALUES (%s, %s, %s, %s)", preset_posts)

        preset_users = [
            (1, "ZhangSan", "zhangsan", "zhangsan@test.com"),
            (2, "LiSi", "lisi", "lisi@test.com"),
        ]
        c.executemany("INSERT INTO users (id, name, username, email) VALUES (%s, %s, %s, %s)", preset_users)
    else:
        if os.path.exists(DB_PATH):
            try:
                os.remove(DB_PATH)
            except PermissionError:
                pass

        c.execute("DROP TABLE IF EXISTS posts")
        c.execute("DROP TABLE IF EXISTS users")
        c.execute("""
            CREATE TABLE posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                body TEXT,
                userId INTEGER
            )
        """)
        c.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name TEXT,
                username TEXT,
                email TEXT
            )
        """)
        preset_posts = [
            (1, "preset_post_1", "Mock_data_1", 1),
            (2, "preset_post_2", "Mock_data_2", 1),
            (3, "preset_post_3", "Mock_data_3", 1),
            (4, "preset_post_4", "Mock_data_4", 1),
        ]
        c.executemany("INSERT INTO posts (id, title, body, userId) VALUES (?, ?, ?, ?)", preset_posts)

        preset_users = [
            (1, "ZhangSan", "zhangsan", "zhangsan@test.com"),
            (2, "LiSi", "lisi", "lisi@test.com"),
        ]
        c.executemany("INSERT INTO users (id, name, username, email) VALUES (?, ?, ?, ?)", preset_users)

    conn.commit()
    conn.close()


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
        c.execute("SELECT * FROM posts WHERE id = %s" if USE_MYSQL else "SELECT * FROM posts WHERE id = ?", (post_id,))
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
        if USE_MYSQL:
            c.execute("INSERT INTO posts (title, body, userId) VALUES (%s, %s, %s)",
                      (data.get('title'), data.get('body'), data.get('userId', 1)))
            conn.commit()
            new_id = c.lastrowid
        else:
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
        ph = "%s" if USE_MYSQL else "?"

        c.execute(f"SELECT * FROM posts WHERE id = {ph}", (post_id,))
        if not c.fetchone():
            return jsonify({"error": "Not found"}), 404

        c.execute(f"SELECT title, body, userId FROM posts WHERE id = {ph}", (post_id,))
        old = c.fetchone()
        new_title = data.get('title', old['title'])
        new_body = data.get('body', old['body'])
        new_userId = data.get('userId', old['userId'])

        c.execute(f"UPDATE posts SET title={ph}, body={ph}, userId={ph} WHERE id={ph}",
                  (new_title, new_body, new_userId, post_id))
        conn.commit()

        c.execute(f"SELECT * FROM posts WHERE id = {ph}", (post_id,))
        row = c.fetchone()
        return jsonify(dict(row))
    finally:
        conn.close()


@app.route('/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    conn = get_db()
    try:
        c = conn.cursor()
        ph = "%s" if USE_MYSQL else "?"
        c.execute(f"SELECT * FROM posts WHERE id = {ph}", (post_id,))
        if not c.fetchone():
            return jsonify({"error": "Not found"}), 404
        c.execute(f"DELETE FROM posts WHERE id = {ph}", (post_id,))
        conn.commit()
        return jsonify({"message": "Deleted"}), 200
    finally:
        conn.close()


@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    conn = get_db()
    try:
        c = conn.cursor()
        ph = "%s" if USE_MYSQL else "?"
        c.execute(f"SELECT * FROM users WHERE id = {ph}", (user_id,))
        row = c.fetchone()
        if row:
            return jsonify(dict(row))
        return jsonify({"error": "Not found"}), 404
    finally:
        conn.close()


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=False)

__all__ = ['app', 'init_db']