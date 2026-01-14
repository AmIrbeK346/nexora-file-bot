import os
import psycopg2
import sqlite3
from datetime import datetime

class Database:
    def __init__(self):
        # Railway serverida 'DATABASE_URL' avtomatik mavjud bo'ladi
        self.db_url = os.getenv("DATABASE_URL")
        self.create_table()

    def get_connection(self):
        # AGAR DATABASE_URL bo'lsa (Serverda), Postgresga ulanadi
        # AGAR bo'lmasa (Kompyuterda), SQLite ishlatadi
        if self.db_url:
            return psycopg2.connect(self.db_url, sslmode='require')
        else:
            return sqlite3.connect("bot_database.db")

    def create_table(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        # PostgreSQL BIGINT va TEXT formatlarini yaxshi tushunadi
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

    def add_user(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        # Postgres va SQLite uchun universal SQL
        placeholder = "%s" if self.db_url else "?"
        
        cursor.execute(f"SELECT user_id FROM users WHERE user_id = {placeholder}", (user_id,))
        if not cursor.fetchone():
            now = datetime.now().strftime("%Y-%m-%d")
            cursor.execute(
                f"INSERT INTO users (user_id, join_date) VALUES ({placeholder}, {placeholder})",
                (user_id, now)
            )
            conn.commit()
        conn.close()

    def get_language(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        placeholder = "%s" if self.db_url else "?"
        cursor.execute(f"SELECT language FROM users WHERE user_id = {placeholder}", (user_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else "uz"

    def set_language(self, user_id, lang):
        conn = self.get_connection()
        cursor = conn.cursor()
        placeholder = "%s" if self.db_url else "?"
        cursor.execute(f"UPDATE users SET language = {placeholder} WHERE user_id = {placeholder}", (lang, user_id))
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
        placeholder = "%s" if self.db_url else "?"
        cursor.execute(f"SELECT COUNT(*) FROM users WHERE join_date = {placeholder}", (today,))
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

db = Database()
