-- MySQL 初始化脚本：创建表 + 预置数据
CREATE TABLE IF NOT EXISTS posts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(255) NOT NULL,
    body TEXT,
    userId INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    username VARCHAR(100),
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 预置文章数据
INSERT INTO posts (id, title, body, userId) VALUES
(1, '预置文章1', 'MySQL数据1', 1),
(2, '预置文章2', 'MySQL数据2', 1),
(3, '预置文章3', 'MySQL数据3', 1),
(4, '预置文章4', 'MySQL数据4', 1);

-- 预置用户数据
INSERT INTO users (id, name, username, email) VALUES
(1, '张三', 'zhangsan', 'zhangsan@test.com'),
(2, '李四', 'lisi', 'lisi@test.com');
