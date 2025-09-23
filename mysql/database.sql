-- 创建数据库
CREATE DATABASE IF NOT EXISTS ai_roleplay CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE ai_roleplay;

-- 角色表
CREATE TABLE characters (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    trait TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 聊天记录表
CREATE TABLE conversations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    character_id INT,
    user_message TEXT,
    ai_message TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE
);

-- 插入测试角色
INSERT INTO characters (name, trait) VALUES 
('鸣人', '热血少年，梦想成为火影，说话充满激情'),
('诸葛亮', '沉稳睿智，出口成章，善用古文'),
('钢铁侠', '幽默自负，科技天才，喜欢调侃');
