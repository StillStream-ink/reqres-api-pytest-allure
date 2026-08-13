# common/db_util.py
import pymysql
from pymysql.cursors import DictCursor

class DBUtil:
    def __init__(self, host, user, password, database, port=3306):
        self.conn = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port,
            charset="utf8mb4"
        )
        self.cursor = self.conn.cursor(DictCursor)

    def query(self, sql, params=None):
        """查询单条/多条，返回字典列表"""
        self.cursor.execute(sql, params)
        return self.cursor.fetchall()

    def execute(self, sql, params=None):
        """增删改"""
        row = self.cursor.execute(sql, params)
        self.conn.commit()
        return row

    def close(self):
        self.cursor.close()
        self.conn.close()
