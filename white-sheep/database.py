import sqlite3

DB_PATH = 'white-sheep.db'

def connect_db():
    return sqlite3.connect(DB_PATH)

def setup_database():
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS users (
                       user_id INTEGER PRIMARY KEY,
                       balance INTEGER DEFAULT 0,
                       last_daily TEXT,
                       streak INTEGER DEFAULT 0,
                       win_rate INTEGER DEFAULT 40,
                       luck INTEGER DEFAULT 0,
                       so_ve INTEGER DEFAULT 0,
                       hsd TEXT,
                       level INTEGER DEFAULT 1,
                       exp INTEGER DEFAULT 0,
                       invite INTEGER DEFAULT 0)
                       ''')
        conn.commit()
        
def get_user_data(user_id):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        return cursor.fetchone()
    
def create_user(user_id, balance=0, last_daily=None, streak=0, win_rate = 40, luck = 0, so_ve = 0, hsd = None, level = 1, exp = 0, invite = 0):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM users WHERE user_id = ?', (user_id,))
        if cursor.fetchone():
            return
        
        cursor.execute('''
                       INSERT INTO users (user_id, balance, last_daily, streak, win_rate, luck, so_ve, hsd, level, exp, invite)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (user_id, balance, last_daily, streak, win_rate, luck, so_ve, hsd, level, exp, invite))
        conn.commit()
        
def update_user_data(user_id, balance, last_daily, streak, win_rate, luck, so_ve, hsd, level, exp, invite):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
                       UPDATE users SET balance = ?, last_daily = ?, streak = ?, win_rate = ?, luck = ?, so_ve = ?, hsd = ?, level = ?, exp = ?, invite = ? WHERE user_id = ?''', (balance, last_daily, streak, win_rate, luck, so_ve, hsd, level, exp, invite, user_id))
        conn.commit()
        
setup_database()