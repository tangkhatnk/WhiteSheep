import sqlite3

# Kết nối đến cơ sở dữ liệu SQLite
def connect_db():
    conn = sqlite3.connect('sheep.db')
    return conn

# Kiểm tra và khởi tạo bảng nếu chưa có
def setup_database():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        balance INTEGER,
        games_played INTEGER DEFAULT 0,
        games_won INTEGER DEFAULT 0,
        win_rate INTEGER DEFAULT 40,
        games_won_in_a_row INTEGER DEFAULT 0,
        luck INTEGER DEFAULT 0 
    )
    ''')
    conn.commit()
    conn.close()

# Lấy dữ liệu người dùng (bao gồm tất cả các trường)
def get_user_data(user_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT balance, games_played, games_won, win_rate, games_won_in_a_row, luck FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result if result else (None, None, None, None, None, None)  # Return (balance, games_played, games_won, win_rate, games_won_in_a_row, luck)

# Cập nhật thông tin người dùng (bao gồm tất cả các trường)
def update_user_data(user_id, new_balance, games_played, games_won, win_rate, games_won_in_a_row, luck):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('REPLACE INTO users (user_id, balance, games_played, games_won, win_rate, games_won_in_a_row, luck) VALUES (?, ?, ?, ?, ?, ?, ?)', 
                   (user_id, new_balance, games_played, games_won, win_rate, games_won_in_a_row, luck))
    conn.commit()
    conn.close()

# Khởi tạo cơ sở dữ liệu
setup_database()
