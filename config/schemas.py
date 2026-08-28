"""
JSON Schema 定义
用于校验接口返回的数据结构
"""

# ==================== 文章模块 ====================
posts_list_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "required": ["id", "title", "body", "userId"],
        "properties": {
            "id": {"type": "integer"},
            "title": {"type": "string"},
            "body": {"type": "string"},
            "userId": {"type": "integer"}
        }
    }
}

post_detail_schema = {
    "type": "object",
    "required": ["id", "title", "body", "userId"],
    "properties": {
        "id": {"type": "integer"},
        "title": {"type": "string"},
        "body": {"type": "string"},
        "userId": {"type": "integer"}
    }
}

post_create_schema = {
    "type": "object",
    "required": ["id", "title", "body", "userId"],
    "properties": {
        "id": {"type": "integer"},
        "title": {"type": "string"},
        "body": {"type": "string"},
        "userId": {"type": "integer"}
    }
}

# ==================== 商品模块 ====================
products_list_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "required": ["id", "name", "price"],
        "properties": {
            "id": {"type": "integer"},
            "name": {"type": "string"},
            "price": {"type": "number"}
        }
    }
}

product_detail_schema = {
    "type": "object",
    "required": ["id", "name", "price"],
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string"},
        "price": {"type": "number"}
    }
}

product_create_schema = {
    "type": "object",
    "required": ["id", "name", "price"],
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string"},
        "price": {"type": "number"}
    }
}

# ==================== 订单模块 ====================
orders_list_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "required": ["id", "user_id", "product_id", "quantity", "status"],
        "properties": {
            "id": {"type": "integer"},
            "user_id": {"type": "integer"},
            "product_id": {"type": "integer"},
            "quantity": {"type": "integer"},
            "status": {"type": "string"}
        }
    }
}

order_detail_schema = {
    "type": "object",
    "required": ["id", "user_id", "product_id", "quantity", "status"],
    "properties": {
        "id": {"type": "integer"},
        "user_id": {"type": "integer"},
        "product_id": {"type": "integer"},
        "quantity": {"type": "integer"},
        "status": {"type": "string"}
    }
}

order_create_schema = {
    "type": "object",
    "required": ["id", "user_id", "product_id", "quantity", "status"],
    "properties": {
        "id": {"type": "integer"},
        "user_id": {"type": "integer"},
        "product_id": {"type": "integer"},
        "quantity": {"type": "integer"},
        "status": {"type": "string"}
    }
}

# ==================== 评论模块 ====================
comments_list_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "required": ["id", "post_id", "content", "user_id"],
        "properties": {
            "id": {"type": "integer"},
            "post_id": {"type": "integer"},
            "content": {"type": "string"},
            "user_id": {"type": "integer"}
        }
    }
}

comment_detail_schema = {
    "type": "object",
    "required": ["id", "post_id", "content", "user_id"],
    "properties": {
        "id": {"type": "integer"},
        "post_id": {"type": "integer"},
        "content": {"type": "string"},
        "user_id": {"type": "integer"}
    }
}

comment_create_schema = {
    "type": "object",
    "required": ["id", "post_id", "content", "user_id"],
    "properties": {
        "id": {"type": "integer"},
        "post_id": {"type": "integer"},
        "content": {"type": "string"},
        "user_id": {"type": "integer"}
    }
}

# ==================== 用户模块 ====================
user_schema = {
    "type": "object",
    "required": ["id", "name", "username", "email"],
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string"},
        "username": {"type": "string"},
        "email": {"type": "string"}
    }
}