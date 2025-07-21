import sqlite3

DB_PATH = 'sheep.db'

# Kết nối đến cơ sở dữ liệu SQLite
def connect_db():
    return sqlite3.connect(DB_PATH)

# Khởi tạo bảng users nếu chưa có
def setup_database():
    """
    Tạo bảng users nếu chưa tồn tại. Bảng gồm các trường:
    user_id, balance, last_daily, streak
    """
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                balance INTEGER DEFAULT 0,
                last_daily TEXT,
                streak INTEGER DEFAULT 0,
                win_rate INTEGER DEFAULT 40,
                luck INTEGER DEFAULT 0
            )
        ''')
        # Thêm cột nếu nâng cấp từ database cũ
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN win_rate INTEGER DEFAULT 40")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN luck INTEGER DEFAULT 35")
        except:
            pass
        conn.commit()
        
# Tạo user mới
def create_user(user_id, balance=0, last_daily=None, streak=0, win_rate = 40, luck = 0):
    """
    Tạo user mới với giá trị mặc định hoặc truyền vào.
    """
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO users (user_id, balance, last_daily, streak, win_rate, luck) VALUES (?, ?, ?, ?, ?, ?)',
            (user_id, balance, last_daily, streak, win_rate, luck)
        )
        conn.commit()

# Lấy dữ liệu người dùng, tự động tạo user mới nếu chưa có
def get_user_data(user_id):
    """
    Lấy dữ liệu user (balance, last_daily, streak).
    Nếu user chưa có, trả về None.
    """
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT balance, last_daily, streak, win_rate, luck FROM users WHERE user_id = ?', (user_id,))
        return cursor.fetchone()

# Cập nhật toàn bộ thông tin user, tự động tạo user mới nếu chưa có
def update_user_data(user_id, balance, last_daily, streak, win_rate, luck):
    """
    Cập nhật toàn bộ thông tin user. Chỉ cập nhật nếu user đã tồn tại.
    """
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM users WHERE user_id = ?', (user_id,))
        if not cursor.fetchone():
            # Không làm gì nếu chưa có user
            return
        cursor.execute(
            'UPDATE users SET balance=?, last_daily=?, streak=?, win_rate=?, luck=? WHERE user_id=?',
            (balance, last_daily, streak, win_rate, luck, user_id)
        )
        conn.commit()


# Khởi tạo database khi import file
setup_database()
