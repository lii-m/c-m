"""
数据库操作模块 - 元气记账本
负责SQLite数据库的连接、表创建和基础CRUD操作
支持多用户数据隔离
"""

import sqlite3
import os
import hashlib
from datetime import datetime

# 数据库文件路径
DB_PATH = os.path.join(os.path.dirname(__file__), 'yuanqi_ledger.db')


def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化数据库，创建表结构（首次运行自动执行）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 消费记录表（添加user_id）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            subcategory TEXT,
            emotion TEXT NOT NULL,
            note TEXT,
            is_income INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # 设置表（添加user_id）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            key TEXT NOT NULL,
            value TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, key)
        )
    ''')
    
    # 成就表（添加user_id）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            icon TEXT DEFAULT '🏆',
            unlocked INTEGER DEFAULT 0,
            unlocked_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, name)
        )
    ''')
    
    # 迁移旧数据（如果没有user_id列）
    try:
        cursor.execute('SELECT user_id FROM expenses LIMIT 1')
    except:
        # 旧数据库，需要重建表结构
        # 创建默认用户
        cursor.execute('''
            INSERT OR IGNORE INTO users (username, password_hash) 
            VALUES ('default', ?)
        ''', (hash_password('default'),))
        
        # 获取默认用户ID
        cursor.execute('SELECT id FROM users WHERE username = ?', ('default',))
        default_user_id = cursor.fetchone()[0]
        
        # 重建 expenses 表（确保列顺序正确）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT,
                emotion TEXT NOT NULL,
                note TEXT,
                is_income INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        cursor.execute(f'''
            INSERT INTO expenses_new (id, user_id, date, amount, category, subcategory, emotion, note, is_income, created_at)
            SELECT id, {default_user_id}, date, amount, category, subcategory, emotion, note, is_income, created_at FROM expenses
        ''')
        cursor.execute('DROP TABLE expenses')
        cursor.execute('ALTER TABLE expenses_new RENAME TO expenses')
        
        # 重建 settings 表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                key TEXT NOT NULL,
                value TEXT,
                UNIQUE(user_id, key),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        cursor.execute(f'''
            INSERT INTO settings_new (id, user_id, key, value)
            SELECT id, {default_user_id}, key, value FROM settings
        ''')
        cursor.execute('DROP TABLE settings')
        cursor.execute('ALTER TABLE settings_new RENAME TO settings')
        
        # 重建 achievements 表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS achievements_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                achievement_key TEXT NOT NULL,
                unlocked INTEGER DEFAULT 0,
                unlocked_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, achievement_key)
            )
        ''')
        cursor.execute(f'''
            INSERT INTO achievements_new (id, user_id, achievement_key, unlocked, unlocked_at)
            SELECT id, {default_user_id}, achievement_key, unlocked, unlocked_at FROM achievements
        ''')
        cursor.execute('DROP TABLE achievements')
        cursor.execute('ALTER TABLE achievements_new RENAME TO achievements')
    
    conn.commit()
    conn.close()


def hash_password(password):
    """密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password, password_hash):
    """验证密码"""
    return hash_password(password) == password_hash


def create_user(username, password):
    """创建新用户"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO users (username, password_hash) VALUES (?, ?)
        ''', (username, hash_password(password)))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        conn.close()
        return None


def login_user(username, password):
    """用户登录验证"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, password_hash FROM users WHERE username = ?', (username,))
    row = cursor.fetchone()
    conn.close()
    
    if row and verify_password(password, row[1]):
        return row[0]
    return None


def get_username(user_id):
    """获取用户名"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


# ========== 消费记录操作（需要user_id） ==========

def add_expense(user_id, date, amount, category, subcategory, emotion, note, is_income=0):
    """添加一条消费记录"""
    conn = get_db_connection()
    cursor = conn.cursor()
    created_at = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO expenses (user_id, date, amount, category, subcategory, emotion, note, is_income, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, date, amount, category, subcategory, emotion, note, is_income, created_at))
    conn.commit()
    conn.close()


def get_expenses(user_id, limit=None):
    """获取用户消费记录，按时间倒序"""
    conn = get_db_connection()
    cursor = conn.cursor()
    if limit:
        cursor.execute('SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC, created_at DESC LIMIT ?', (user_id, limit))
    else:
        cursor.execute('SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC, created_at DESC', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [tuple(row) for row in rows]


def get_expenses_by_date_range(user_id, start_date, end_date):
    """获取指定日期范围的记录"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM expenses 
        WHERE user_id = ? AND date >= ? AND date <= ?
        ORDER BY date DESC
    ''', (user_id, start_date, end_date))
    rows = cursor.fetchall()
    conn.close()
    return [tuple(row) for row in rows]


def get_monthly_expenses(user_id, year, month):
    """获取指定年月的所有记录"""
    start_date = f"{year}-{month:02d}-01"
    if month == 12:
        end_date = f"{year + 1}-01-01"
    else:
        end_date = f"{year}-{month + 1:02d}-01"
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM expenses 
        WHERE user_id = ? AND date >= ? AND date < ?
        ORDER BY date DESC, created_at DESC
    ''', (user_id, start_date, end_date))
    rows = cursor.fetchall()
    conn.close()
    return [tuple(row) for row in rows]


def get_total_monthly_expense(user_id, year, month):
    """计算指定年月总消费（排除收入）"""
    start_date = f"{year}-{month:02d}-01"
    if month == 12:
        end_date = f"{year + 1}-01-01"
    else:
        end_date = f"{year}-{month + 1:02d}-01"
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0) FROM expenses 
        WHERE user_id = ? AND date >= ? AND date < ? AND is_income = 0
    ''', (user_id, start_date, end_date))
    result = cursor.fetchone()[0]
    conn.close()
    return result


def get_total_monthly_income(user_id, year, month):
    """计算指定年月总收入"""
    start_date = f"{year}-{month:02d}-01"
    if month == 12:
        end_date = f"{year + 1}-01-01"
    else:
        end_date = f"{year}-{month + 1:02d}-01"
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0) FROM expenses 
        WHERE user_id = ? AND date >= ? AND date < ? AND is_income = 1
    ''', (user_id, start_date, end_date))
    result = cursor.fetchone()[0]
    conn.close()
    return result


def get_daily_expense(user_id, date_str):
    """获取指定日期总消费（排除收入）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0) FROM expenses 
        WHERE user_id = ? AND date = ? AND is_income = 0
    ''', (user_id, date_str))
    result = cursor.fetchone()[0]
    conn.close()
    return result


def get_most_expensive(user_id, year, month):
    """获取指定年月最贵的一笔消费（排除收入）"""
    start_date = f"{year}-{month:02d}-01"
    if month == 12:
        end_date = f"{year + 1}-01-01"
    else:
        end_date = f"{year}-{month + 1:02d}-01"
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM expenses 
        WHERE user_id = ? AND date >= ? AND date < ? AND is_income = 0
        ORDER BY amount DESC
        LIMIT 1
    ''', (user_id, start_date, end_date))
    row = cursor.fetchone()
    conn.close()
    return tuple(row) if row else None


def update_expense(expense_id, user_id, date, amount, category, subcategory, emotion, note, is_income=0):
    """更新消费记录"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE expenses 
        SET date=?, amount=?, category=?, subcategory=?, emotion=?, note=?, is_income=?
        WHERE id=? AND user_id=?
    ''', (date, amount, category, subcategory, emotion, note, is_income, expense_id, user_id))
    conn.commit()
    conn.close()


def delete_expense(expense_id, user_id):
    """删除消费记录"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM expenses WHERE id=? AND user_id=?', (expense_id, user_id))
    conn.commit()
    conn.close()


def get_expense_by_id(expense_id, user_id):
    """根据ID获取消费记录"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM expenses WHERE id=? AND user_id=?', (expense_id, user_id))
    row = cursor.fetchone()
    conn.close()
    return tuple(row) if row else None


# ========== 设置操作（需要user_id） ==========

def get_setting(user_id, key):
    """获取用户设置项"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM settings WHERE user_id = ? AND key = ?', (user_id, key))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def set_setting(user_id, key, value):
    """设置用户配置项"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO settings (user_id, key, value) VALUES (?, ?, ?)
    ''', (user_id, key, str(value)))
    conn.commit()
    conn.close()


# ========== 成就操作（需要user_id） ==========

def get_all_achievements(user_id):
    """获取用户所有成就状态"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT name, unlocked, unlocked_at FROM achievements WHERE user_id = ?', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return {row[0]: {'unlocked': row[1], 'unlocked_at': row[2]} for row in rows}


def unlock_achievement(user_id, name):
    """解锁用户成就"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 从 game_logic 获取成就描述和图标
    from game_logic import ACHIEVEMENTS
    achievement_info = ACHIEVEMENTS.get(name, {})
    description = achievement_info.get('desc', '')
    icon = achievement_info.get('icon', '🏆')
    
    cursor.execute('''
        INSERT OR REPLACE INTO achievements (user_id, name, description, icon, unlocked, unlocked_at)
        VALUES (?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
    ''', (user_id, name, description, icon))
    conn.commit()
    conn.close()


# ========== 迁移旧数据到新用户 ==========

def migrate_to_user(original_user_id, target_user_id):
    """将数据迁移到目标用户"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 迁移 expenses
    cursor.execute('UPDATE expenses SET user_id = ? WHERE user_id = ?', (target_user_id, original_user_id))
    
    # 迁移 settings
    cursor.execute('UPDATE settings SET user_id = ? WHERE user_id = ?', (target_user_id, original_user_id))
    
    # 迁移 achievements
    cursor.execute('UPDATE achievements SET user_id = ? WHERE user_id = ?', (target_user_id, original_user_id))
    
    conn.commit()
    conn.close()


# 首次导入时初始化数据库
init_db()
