from flask import Flask, request, jsonify
import pymysql
from pymysql.cursors import DictCursor

app = Flask(__name__)

# ========== 和你yaml里数据库配置保持一致！XAMPP root空密码 ==========
def get_db_conn():
    conn = pymysql.connect(
        host="127.0.0.1",
        user="root",
        password="",
        database="api_test_db",
        port=3306,
        charset="utf8mb4",
        cursorclass=DictCursor
    )
    return conn

# 1. 获取文章列表 GET /posts
@app.route("/posts", methods=["GET"])
def get_post_list():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM posts;")
    data = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(data)

# 2. 获取单篇文章 GET /posts/<post_id>
@app.route("/posts/<int:post_id>", methods=["GET"])
def get_single_post(post_id):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM posts WHERE id=%s", (post_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return jsonify(row)
    return jsonify({"msg":"不存在"}),404

# 3. 新增文章 POST /posts ✅【核心，自动入库】
@app.route("/posts", methods=["POST"])
def create_post():
    body = request.get_json()
    title = body.get("title")
    body_text = body.get("body")
    user_id = body.get("userId")

    conn = get_db_conn()
    cur = conn.cursor()
    sql = """INSERT INTO posts(title,body,userId) VALUES(%s,%s,%s)"""
    cur.execute(sql, (title, body_text, user_id))
    conn.commit()
    new_id = cur.lastrowid  # 获取自增id
    cur.close()
    conn.close()

    # 返回格式和jsonplaceholder保持一致，你的自动化脚本几乎不用改！
    return jsonify({
        "id": new_id,
        "title": title,
        "body": body_text,
        "userId": user_id
    }), 201

# 4. 修改文章 PUT /posts/<post_id> ✅【核心，更新数据库】
@app.route("/posts/<int:post_id>", methods=["PUT"])
def update_post(post_id):
    body = request.get_json()
    title = body.get("title")
    body_text = body.get("body")
    user_id = body.get("userId")

    conn = get_db_conn()
    cur = conn.cursor()
    sql = """UPDATE posts SET title=%s,body=%s,userId=%s WHERE id=%s"""
    cur.execute(sql, (title, body_text, user_id, post_id))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({
        "id": post_id,
        "title": title,
        "body": body_text,
        "userId": user_id
    })

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
