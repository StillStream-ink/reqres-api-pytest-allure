"""
数据库双检公共工具
统一封装接口返回后的数据库校验逻辑
"""
import allure
from common.mock_server import get_db, USE_MYSQL


def check_db_record(table_name, record_id, expected_fields, id_column="id"):
    ph = "%s" if USE_MYSQL else "?"
    conn = get_db()
    try:
        cursor = conn.cursor()
        fields = list(expected_fields.keys())
        fields_str = ", ".join(fields)
        cursor.execute(
            f"SELECT {fields_str} FROM {table_name} WHERE {id_column} = {ph}",
            (record_id,)
        )
        row = cursor.fetchone()
        if row:
            row_dict = dict(row) if hasattr(row, 'keys') else {fields[i]: row[i] for i in range(len(fields))}
        else:
            row_dict = None
        allure.attach(str(row_dict), f"{table_name}数据库记录", allure.attachment_type.JSON)
        return row_dict
    finally:
        conn.close()


def assert_db_record(row_dict, expected_fields):
    assert row_dict is not None, "数据库中未找到该记录"
    for key, expected_value in expected_fields.items():
        actual_value = row_dict.get(key)
        if isinstance(expected_value, float):
            assert round(actual_value, 2) == round(expected_value, 2), \
                f"字段【{key}】值不一致！预期:{expected_value}，实际:{actual_value}"
        else:
            assert actual_value == expected_value, \
                f"字段【{key}】值不一致！预期:{expected_value}，实际:{actual_value}"


def check_and_assert(table_name, record_id, expected_fields, id_column="id"):
    row_dict = check_db_record(table_name, record_id, expected_fields, id_column)
    assert_db_record(row_dict, expected_fields)
    return row_dict