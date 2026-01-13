import sqlite3
from datetime import datetime
from config import DB_PATH

class Database:
     def __init__(self, db_name=DB_PATH):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        # Foydalanuvchilar jadvali: ID va qo'shilgan vaqti
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                join_date TEXT
            )
        """)
        self.conn.commit()

    def add_user(self, user_id):
        # Foydalanuvchi bazada bormi tekshiramiz
        self.cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if not self.cursor.fetchone():
            now = datetime.now().strftime("%Y-%m-%d")
            self.cursor.execute("INSERT INTO users (user_id, join_date) VALUES (?, ?)", (user_id, now))
            self.conn.commit()

    def count_total_users(self):
        self.cursor.execute("SELECT COUNT(*) FROM users")
        return self.cursor.fetchone()[0]

    def count_today_users(self):
        today = datetime.now().strftime("%Y-%m-%d")
        self.cursor.execute("SELECT COUNT(*) FROM users WHERE join_date = ?", (today,))
        return self.cursor.fetchone()[0]

    def get_all_users(self):
        self.cursor.execute("SELECT user_id FROM users")
        return [row[0] for row in self.cursor.fetchall()]

db = Database() # Baza bilan ishlash uchun obyekt
