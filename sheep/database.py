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
                luck INTEGER DEFAULT 0,
                so_ve INTEGER DEFAULT 0,
                hsd TEXT,
                level INTEGER DEFAULT 1,
                exp INTEGER DEFAULT 0,
                invite INTEGER DEFAULT 0
            )
        ''')

        conn.commit()
        
# Tạo user mới
def create_user(user_id, balance=0, last_daily=None, streak=0, win_rate = 40, luck = 0, level=1, exp=0, invite=0):
    """
    Tạo user mới với giá trị mặc định hoặc truyền vào.
    """
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO users (user_id, balance, last_daily, streak, win_rate, luck, level, exp, invite) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (user_id, balance, last_daily, streak, win_rate, luck, level, exp, invite)
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
        cursor.execute('SELECT balance, last_daily, streak, win_rate, luck, so_ve, hsd, level, exp, invite FROM users WHERE user_id = ?', (user_id,))
        return cursor.fetchone()

# Cập nhật toàn bộ thông tin user, tự động tạo user mới nếu chưa có
def update_user_data(user_id, balance, last_daily, streak, win_rate, luck, so_ve, hsd, level, exp, invite):
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
            'UPDATE users SET balance=?, last_daily=?, streak=?, win_rate=?, luck=?, so_ve=?, hsd=?, level=?, exp=?, invite=? WHERE user_id=?',
            (balance, last_daily, streak, win_rate, luck, so_ve, hsd, level, exp, invite, user_id)
        )
        conn.commit()

# Hàm tự động cập nhật bảng users nếu thiếu trường mới
def migrate_database():
    with connect_db() as conn:
        cursor = conn.cursor()
        # Lấy thông tin các cột hiện tại
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        # Thêm trường level nếu chưa có
        if 'level' not in columns:
            cursor.execute('ALTER TABLE users ADD COLUMN level INTEGER DEFAULT 1')
        # Thêm trường exp nếu chưa có
        if 'exp' not in columns:
            cursor.execute('ALTER TABLE users ADD COLUMN exp INTEGER DEFAULT 0')
        # Thêm trường invite_count nếu chưa có
        if 'invite' not in columns:
            cursor.execute('ALTER TABLE users ADD COLUMN invite INTEGER DEFAULT 0')
        conn.commit()


# Khởi tạo database khi import file
setup_database()
migrate_database()
