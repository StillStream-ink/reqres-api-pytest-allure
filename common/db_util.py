import pymysql
from pymysql.cursors import DictCursor
from common.log_util import logger

import pymysql

class DBUtil:
    def __init__(self, host, user, password, database, port=3306):
        self.conn = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor  # 返回字典，方便断言取值
        )
        self.cursor = self.conn.cursor()

    def query_one(self, sql):
        """查询单条记录"""
        self.cursor.execute(sql)
        return self.cursor.fetchone()

    def close(self):
        self.cursor.close()
        self.conn.close()
