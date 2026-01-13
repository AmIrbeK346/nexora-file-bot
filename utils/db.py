import os
import psycopg2
import sqlite3
from datetime import datetime

class Database:
    def __init__(self):
        # Railway DATABASE_URL ni avtomatik beradi
        self.db_url = os.getenv("DATABASE_URL")
        self.create_table()

    def get_connection(self):
        if self.db_url:
            # Serverda Postgres ishlatamiz
            return psycopg2.connect(self.db_url)
        else:
            # Kompyuterda SQLite ishlatamiz
            return sqlite3.connect("bot_database.db")

    def create_table(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        # Postgres va SQLite uchun mos keladigan SQL
        query = """
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                join_date TEXT
            )
        """
        cursor.execute(query)
        conn.commit()
        conn.close()

    def add_user(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        # Foydalanuvchi borligini tekshirish
        cursor.execute("SELECT user_id FROM users WHERE user_id = %s" if self.db_url else "SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if not cursor.fetchone():
            now = datetime.now().strftime("%Y-%m-%d")
            sql = "INSERT INTO users (user_id, join_date) VALUES (%s, %s)" if self.db_url else "INSERT INTO users (user_id, join_date) VALUES (?, ?)"
            cursor.execute(sql, (user_id, now))
            conn.commit()
        conn.close()

    def count_total_users(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def count_today_users(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        sql = "SELECT COUNT(*) FROM users WHERE join_date = %s" if self.db_url else "SELECT COUNT(*) FROM users WHERE join_date = ?"
        cursor.execute(sql, (today,))
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def get_all_users(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users")
        users = [row[0] for row in cursor.fetchall()]
        conn.close()
        return users

    def set_language(self, user_id, lang):
        conn = self.get_connection()
        cursor = conn.cursor()
        # Avval foydalanuvchi borligini tekshiramiz (add_user funksiyasini ham chaqirib ketadi)
        self.add_user(user_id)
        
        sql = "UPDATE users SET language = %s WHERE user_id = %s" if self.db_url else "UPDATE users SET language = ? WHERE user_id = ?"
        cursor.execute(sql, (lang, user_id))
        conn.commit()
        conn.close()

    def get_language(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        sql = "SELECT language FROM users WHERE user_id = %s" if self.db_url else "SELECT language FROM users WHERE user_id = ?"
        cursor.execute(sql, (user_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row and row[0] else "uz" # Default uz
        
    def create_table(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        query = """
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                join_date TEXT,
                language TEXT DEFAULT 'uz'
            )
        """
        cursor.execute(query)
        conn.commit()
        conn.close()
db = Database()
