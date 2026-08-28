-- MySQL 初始化脚本：创建表 + 预置数据（适配 Docker 环境）
-- 包含文章、用户、商品、订单 四个模块

-- ==================== 1. 文章表 ====================
CREATE TABLE IF NOT EXISTS posts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(255) NOT NULL,
    body TEXT,
    userId INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==================== 2. 用户表 ====================
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    username VARCHAR(100),
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==================== 3. 商品表 ====================
CREATE TABLE IF NOT EXISTS products (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    price DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==================== 4. 订单表 ====================
CREATE TABLE IF NOT EXISTS orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    product_id INT,
    quantity INT,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 预置数据
-- ============================================================

-- 预置文章数据（4篇）
INSERT INTO posts (id, title, body, userId) VALUES
(1, '预置文章1', 'MySQL数据1', 1),
(2, '预置文章2', 'MySQL数据2', 1),
(3, '预置文章3', 'MySQL数据3', 1),
(4, '预置文章4', 'MySQL数据4', 1);

-- 预置用户数据（2个）
INSERT INTO users (id, name, username, email) VALUES
(1, '张三', 'zhangsan', 'zhangsan@test.com'),
(2, '李四', 'lisi', 'lisi@test.com');

-- 预置商品数据（2个）
INSERT INTO products (id, name, price) VALUES
(1, '智能手表', 299.00),
(2, '无线耳机', 89.00);

-- 预置订单数据（2条）
INSERT INTO orders (id, user_id, product_id, quantity, status) VALUES
(1, 1, 1, 2, 'pending'),
(2, 2, 2, 1, 'shipped');