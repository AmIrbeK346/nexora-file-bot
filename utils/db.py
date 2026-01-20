import os
import sqlite3
import logging
from datetime import datetime

# Faqat serverda Postgres ishlatish uchun psycopg2 ni yuklaymiz
try:
    import psycopg2
except ImportError:
    psycopg2 = None

class Database:
    def __init__(self):
        # Railway-dagi o'zgaruvchini tekshiramiz
        self.db_url = os.getenv("DATABASE_URL")
        self.create_table()

    def get_connection(self):
        # Agar DATABASE_URL bo'lsa va psycopg2 o'rnatilgan bo'lsa Postgresga ulanadi
        if self.db_url and psycopg2:
            try:
                return psycopg2.connect(self.db_url, sslmode='require')
            except Exception as e:
                logging.error(f"Postgres ulanishda xato, SQLite-ga o'tilmoqda: {e}")
        
        # Har qanday boshqa holatda SQLite ishlatiladi
        return sqlite3.connect("bot_database.db")

    def create_table(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        # Ikkala baza uchun ham tushunarli bo'lgan SQL
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
        now = datetime.now().strftime("%Y-%m-%d")
        
        try:
            if self.db_url and psycopg2 and not isinstance(conn, sqlite3.Connection):
                # Postgres uchun mantiq
                query = "INSERT INTO users (user_id, join_date) VALUES (%s, %s) ON CONFLICT (user_id) DO NOTHING"
                cursor.execute(query, (user_id, now))
            else:
                # SQLite uchun mantiq (Sizda xato bergan joy shu yer edi)
                cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
                if not cursor.fetchone():
                    cursor.execute("INSERT INTO users (user_id, join_date) VALUES (?, ?)", (user_id, now))
            conn.commit()
        except Exception as e:
            logging.error(f"Foydalanuvchi qo'shishda xato: {e}")
        finally:
            conn.close()

    def get_language(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        placeholder = "%s" if (self.db_url and not isinstance(conn, sqlite3.Connection)) else "?"
        try:
            cursor.execute(f"SELECT language FROM users WHERE user_id = {placeholder}", (user_id,))
            row = cursor.fetchone()
            return row[0] if row and row[0] else "uz"
        finally:
            conn.close()

    def set_language(self, user_id, lang):
        conn = self.get_connection()
        cursor = conn.cursor()
        placeholder = "%s" if (self.db_url and not isinstance(conn, sqlite3.Connection)) else "?"
        try:
            # Avval foydalanuvchi borligini tekshirish
            self.add_user(user_id)
            cursor.execute(f"UPDATE users SET language = {placeholder} WHERE user_id = {placeholder}", (lang, user_id))
            conn.commit()
        finally:
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
        placeholder = "%s" if (self.db_url and not isinstance(conn, sqlite3.Connection)) else "?"
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
