from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'test_mock.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初始化数据库，每次启动重置"""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            body TEXT,
            userId INTEGER
        )
    ''')
    c.execute("INSERT INTO posts (title, body, userId) VALUES (?, ?, ?)", 
              ("hello", "world", 1))
    c.execute("INSERT INTO posts (title, body, userId) VALUES (?, ?, ?)", 
              ("foo", "bar", 1))
    conn.commit()
    conn.close()

@app.route('/posts', methods=['GET'])
def get_posts():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM posts")
    rows = c.fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

@app.route('/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return jsonify(dict(row))
    return jsonify({"error": "Not found"}), 404

@app.route('/posts', methods=['POST'])
def create_post():
    data = request.get_json()
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO posts (title, body, userId) VALUES (?, ?, ?)",
              (data.get('title'), data.get('body'), data.get('userId', 1)))
    conn.commit()
    new_id = c.lastrowid
    conn.close()
    return jsonify({
        "id": new_id,
        "title": data.get('title'),
        "body": data.get('body'),
        "userId": data.get('userId', 1)
    }), 201

@app.route('/posts/<int:post_id>', methods=['PUT'])
def update_post(post_id):
    data = request.get_json()
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
    if not c.fetchone():
        conn.close()
        return jsonify({"error": "Not found"}), 404
    c.execute("UPDATE posts SET title=?, body=?, userId=? WHERE id=?",
              (data.get('title'), data.get('body'), data.get('userId', 1), post_id))
    conn.commit()
    c.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
    row = c.fetchone()
    conn.close()
    return jsonify(dict(row))

@app.route('/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    conn.commit()
    deleted = c.rowcount
    conn.close()
    if deleted:
        return jsonify({"message": "Deleted"}), 200
    return jsonify({"error": "Not found"}), 404

if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', port=5000, debug=False)

__all__ = ['app', 'init_db', 'DB_PATH']