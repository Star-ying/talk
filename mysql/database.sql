-- Active: 1760836081728@@127.0.0.1@3306@ai_roleplay
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

--用户信息表
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    account VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL
)

CREATE TABLE user_profiles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) UNIQUE NOT NULL,         -- 用户唯一标识（如 session 或登录 ID）
    personality TEXT,                            -- 性格描述
    role_setting TEXT,                           -- 角色设定（prompt）
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP
);

-- 表名: user_settings
CREATE TABLE `user_settings` (
  `user_id` VARCHAR(50) PRIMARY KEY,
  `role_setting` TEXT ,
  `max_history` INT DEFAULT 4,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 插入默认值
INSERT INTO user_settings (user_id, role_setting) 
VALUES ('user123', '你正在扮演一位聪明、幽默又略带毒舌的程序员助手...');