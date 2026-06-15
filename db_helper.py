"""
数据库操作模块 - 元气记账本
负责SQLite数据库的连接、表创建和基础CRUD操作
"""

import sqlite3
import os
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
    
    # 消费记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            subcategory TEXT,
            emotion TEXT NOT NULL,
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 设置表（预算等）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    # 成就表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            unlocked INTEGER DEFAULT 0,
            unlocked_at TIMESTAMP
        )
    ''')
    
    # 初始化默认设置
    cursor.execute('''
        INSERT OR IGNORE INTO settings (key, value) VALUES ('monthly_budget', '2000')
    ''')
    
    conn.commit()
    conn.close()


def add_expense(date, amount, category, subcategory, emotion, note):
    """添加一条消费记录"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO expenses (date, amount, category, subcategory, emotion, note)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (date, amount, category, subcategory, emotion, note))
    conn.commit()
    conn.close()


def get_expenses(limit=None):
    """获取消费记录，按时间倒序"""
    conn = get_db_connection()
    cursor = conn.cursor()
    if limit:
        cursor.execute('SELECT * FROM expenses ORDER BY date DESC, created_at DESC LIMIT ?', (limit,))
    else:
        cursor.execute('SELECT * FROM expenses ORDER BY date DESC, created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return [tuple(row) for row in rows]


def get_expenses_by_date_range(start_date, end_date):
    """获取指定日期范围的记录"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM expenses 
        WHERE date >= ? AND date <= ?
        ORDER BY date DESC
    ''', (start_date, end_date))
    rows = cursor.fetchall()
    conn.close()
    return [tuple(row) for row in rows]


def get_monthly_expenses(year, month):
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
        WHERE date >= ? AND date < ?
        ORDER BY date DESC, created_at DESC
    ''', (start_date, end_date))
    rows = cursor.fetchall()
    conn.close()
    return [tuple(row) for row in rows]


def get_total_monthly_expense(year, month):
    """计算指定年月总消费"""
    start_date = f"{year}-{month:02d}-01"
    if month == 12:
        end_date = f"{year + 1}-01-01"
    else:
        end_date = f"{year}-{month + 1:02d}-01"
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0) FROM expenses 
        WHERE date >= ? AND date < ?
    ''', (start_date, end_date))
    result = cursor.fetchone()[0]
    conn.close()
    return result


def get_daily_expense(date_str):
    """获取指定日期总消费"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE date = ?
    ''', (date_str,))
    result = cursor.fetchone()[0]
    conn.close()
    return result


def get_most_expensive(year, month):
    """获取指定年月最贵的一笔消费"""
    start_date = f"{year}-{month:02d}-01"
    if month == 12:
        end_date = f"{year + 1}-01-01"
    else:
        end_date = f"{year}-{month + 1:02d}-01"
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM expenses 
        WHERE date >= ? AND date < ?
        ORDER BY amount DESC
        LIMIT 1
    ''', (start_date, end_date))
    row = cursor.fetchone()
    conn.close()
    return tuple(row) if row else None


def get_setting(key):
    """获取设置项"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def set_setting(key, value):
    """设置配置项"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
    ''', (key, str(value)))
    conn.commit()
    conn.close()


def get_all_achievements():
    """获取所有成就状态"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT name, unlocked, unlocked_at FROM achievements')
    rows = cursor.fetchall()
    conn.close()
    return {row[0]: {'unlocked': row[1], 'unlocked_at': row[2]} for row in rows}


def unlock_achievement(name):
    """解锁成就"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO achievements (name, unlocked, unlocked_at)
        VALUES (?, 1, CURRENT_TIMESTAMP)
    ''', (name,))
    conn.commit()
    conn.close()


# 首次导入时初始化数据库
init_db()
