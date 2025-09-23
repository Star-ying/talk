# backend/database.py
import mysql.connector
from mysql.connector import Error
import os

db_config = {
    'host': 'localhost', #主机地址
    'database': 'ai_roleplay', #数据库名
    'user': 'root',  # 用户名
    'password': '123456'  # 密码
}

def get_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except Error as e:
        print(f"数据库连接失败: {e}")
        return None

def get_all_characters():
    conn = get_connection()
    if conn is None:
        return []
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM characters ORDER BY name")
    result = cursor.fetchall()
    conn.close()
    return result

def save_conversation(character_id, user_msg, ai_msg):
    conn = get_connection()
    if conn is None:
        return
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO conversations (character_id, user_message, ai_message) VALUES (%s, %s, %s)",
        (character_id, user_msg, ai_msg)
    )
    conn.commit()
    conn.close()
