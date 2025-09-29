# backend/database.py
import mysql.connector
from mysql.connector import Error

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
    
def check_users(account,password):
    conn = get_connection()
    if conn is None:
        return []
    cursor = conn.cursor()
    cursor.execute(
            """ SELECT NULL AS id, NULL AS password 
                WHERE NOT EXISTS (SELECT 1 FROM users WHERE account = %s) 
                UNION 
                SELECT id, password
                FROM users 
                WHERE account = %s
                GROUP BY id;"""
        ,(account,account)
    )
    result = cursor.fetchone()
    id = result[0]
    if result[1]:
        password = result[1]
        conn.close()
        return (id,password)
    cursor.execute(
        " INSERT INTO users (account, password) VALUES (%s,%s);",
        (account,password)
    )
    conn.commit()
    cursor.execute("SELECT LAST_INSERT_ID();" )
    id = cursor.fetchone()[0]
    cursor.execute(
        """ CREATE TABLE conversitions_{} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            character_id INT,
            user_message TEXT,
            ai_message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE
        ); """.format(id)
    )
    conn.commit()
    conn.close()
    return (id,password)

def get_all_characters():
    conn = get_connection()
    if conn is None:
        return []
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM characters ORDER BY name")
    result = cursor.fetchall()
    conn.close()
    return result

def save_conversation(user_id,character_id, user_msg, ai_msg):
    conn = get_connection()
    if conn is None:
        return
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO conversitions_{} (character_id, user_message, ai_message) VALUES (%s, %s, %s)".format(user_id),
        (character_id, user_msg, ai_msg)
    )
    conn.commit()
    conn.close()

def get_character_by_id(character_id:int):
    # 查询角色信息
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT name, trait FROM characters WHERE id = %s", (character_id,))
    character = cursor.fetchone()
    conn.close()
    return character