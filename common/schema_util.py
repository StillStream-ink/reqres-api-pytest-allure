"""
JSON Schema 校验工具
"""
import allure
from jsonschema import validate, ValidationError


def validate_schema(response_data, schema, schema_name="响应"):
    """
    校验 JSON 响应是否符合 Schema
    """
    try:
        validate(instance=response_data, schema=schema)
        allure.attach(f"✅ {schema_name} Schema 校验通过", name="Schema校验结果", attachment_type=allure.attachment_type.TEXT)
        return True
    except ValidationError as e:
        error_msg = f"❌ {schema_name} Schema 校验失败: {e.message}"
        allure.attach(error_msg, name="Schema校验结果", attachment_type=allure.attachment_type.TEXT)
        raise AssertionError(error_msg)


def validate_with_step(response_data, schema, schema_name="响应"):
    """带 allure 步骤的校验"""
    with allure.step(f"校验 {schema_name} 数据结构"):
        return validate_schema(response_data, schema, schema_name)