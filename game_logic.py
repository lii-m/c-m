"""
游戏化逻辑模块 - 元气记账本
负责成就系统、预算进度、宠物心情等游戏化功能
"""

from datetime import datetime, timedelta
from db_helper import (
    get_expenses, get_monthly_expenses, get_total_monthly_expense,
    get_setting, set_setting, get_all_achievements, unlock_achievement
)

# 成就定义
ACHIEVEMENTS = {
    'first_record': {
        'name': '记账新手',
        'icon': '🌱',
        'desc': '记录人生第一笔消费'
    },
    'saving_master': {
        'name': '省钱小能手',
        'icon': '💰',
        'desc': '连续7天日均消费低于50元'
    },
    'emotion_master': {
        'name': '情绪大师',
        'icon': '🎭',
        'desc': '使用过全部5种情绪标签'
    },
    'category_master': {
        'name': '分类达人',
        'icon': '📂',
        'desc': '使用过全部10个一级分类'
    },
    'night_shopper': {
        'name': '深夜剁手',
        'icon': '🌙',
        'desc': '晚上10点后记账超过3次'
    },
    'early_bird': {
        'name': '早起鸟',
        'icon': '🐦',
        'desc': '早上8点前记账超过3次'
    },
    'streak_7': {
        'name': '连续打卡',
        'icon': '🔥',
        'desc': '连续7天每天都有记账'
    },
    'small_spender': {
        'name': '精打细算',
        'icon': '🧐',
        'desc': '记录过1元以下的小额消费'
    },
    'big_spender': {
        'name': '大手笔',
        'icon': '💎',
        'desc': '单笔消费超过500元'
    },
    'monthly_champ': {
        'name': '月度冠军',
        'icon': '🏆',
        'desc': '单月记录超过30笔消费'
    }
}


def get_monthly_summary(year=None, month=None):
    """获取月度消费摘要"""
    now = datetime.now()
    year = year or now.year
    month = month or now.month
    
    expenses = get_monthly_expenses(year, month)
    total = get_total_monthly_expense(year, month)
    
    return {
        'total': total,
        'count': len(expenses),
        'category_totals': {}
    }


def calculate_budget_progress():
    """计算预算进度（返回0.0-1.0的小数）"""
    now = datetime.now()
    year = now.year
    month = now.month
    
    total_expense = get_total_monthly_expense(year, month)
    budget = float(get_setting('monthly_budget') or 2000)
    
    progress = min(1.0, total_expense / budget)
    remaining = max(0, budget - total_expense)
    over_budget = total_expense > budget
    
    return {
        'progress': progress,
        'remaining': remaining,
        'total': total_expense,
        'budget': budget,
        'over_budget': over_budget
    }


def get_pet_mood():
    """根据消费情况获取宠物心情和表情"""
    now = datetime.now()
    budget_info = calculate_budget_progress()
    
    # 获取本月后悔消费比例
    month_expenses = get_monthly_expenses(now.year, now.month)
    regret_count = sum(1 for e in month_expenses if e[5] == '😔后悔')
    total_count = len(month_expenses)
    
    regret_ratio = regret_count / total_count if total_count > 0 else 0
    
    if budget_info['over_budget'] or regret_ratio > 0.3:
        return '难过', '😿'
    elif budget_info['progress'] > 0.8 or regret_ratio > 0.15:
        return '正常', '🐱'
    else:
        return '开心', '😺'


def check_saving_master():
    """检查省钱小能手成就"""
    expenses = get_expenses()
    if not expenses:
        return False
    
    # 按日期分组计算日均消费
    daily_totals = {}
    for e in expenses:
        date = e[1]
        daily_totals[date] = daily_totals.get(date, 0) + e[2]
    
    # 检查连续7天
    dates = sorted(daily_totals.keys())
    if len(dates) < 7:
        return False
    
    for i in range(len(dates) - 6):
        week_dates = dates[i:i+7]
        week_total = sum(daily_totals[d] for d in week_dates)
        if week_total / 7 < 50:
            return True
    return False


def check_emotion_master():
    """检查情绪大师成就"""
    expenses = get_expenses()
    emotions = set(e[5] for e in expenses)
    return len(emotions) >= 5


def check_category_master():
    """检查分类达人成就"""
    expenses = get_expenses()
    categories = set(e[3] for e in expenses)
    return len(categories) >= 10


def parse_datetime(time_str):
    """解析时间字符串，支持多种格式"""
    formats = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S']
    for fmt in formats:
        try:
            return datetime.strptime(time_str, fmt)
        except ValueError:
            continue
    # 如果都不行，尝试使用 fromisoformat
    try:
        return datetime.fromisoformat(time_str)
    except ValueError:
        return datetime.now()


def check_night_shopper():
    """检查深夜剁手成就"""
    expenses = get_expenses()
    night_count = sum(1 for e in expenses 
                      if parse_datetime(e[7]).hour >= 22)
    return night_count >= 3


def check_early_bird():
    """检查早起鸟成就"""
    expenses = get_expenses()
    early_count = sum(1 for e in expenses 
                      if parse_datetime(e[7]).hour < 8)
    return early_count >= 3


def check_first_record():
    """检查记账新手成就"""
    expenses = get_expenses()
    return len(expenses) >= 1


def check_streak_7():
    """检查连续打卡成就"""
    expenses = get_expenses()
    if not expenses:
        return False
    
    dates = sorted(set(e[1] for e in expenses))
    if len(dates) < 7:
        return False
    
    for i in range(len(dates) - 6):
        week_dates = dates[i:i+7]
        valid = True
        for j in range(6):
            d1 = datetime.strptime(week_dates[j], '%Y-%m-%d')
            d2 = datetime.strptime(week_dates[j+1], '%Y-%m-%d')
            if (d2 - d1).days != 1:
                valid = False
                break
        if valid:
            return True
    return False


def check_small_spender():
    """检查精打细算成就"""
    expenses = get_expenses()
    return any(e[2] < 1 for e in expenses)


def check_big_spender():
    """检查大手笔成就"""
    expenses = get_expenses()
    return any(e[2] >= 500 for e in expenses)


def check_monthly_champ():
    """检查月度冠军成就"""
    now = datetime.now()
    month_expenses = get_monthly_expenses(now.year, now.month)
    return len(month_expenses) >= 30


def check_all_achievements():
    """检查所有成就，返回新解锁的成就列表"""
    existing = get_all_achievements()
    newly_unlocked = []
    
    checks = {
        'first_record': check_first_record,
        'saving_master': check_saving_master,
        'emotion_master': check_emotion_master,
        'category_master': check_category_master,
        'night_shopper': check_night_shopper,
        'early_bird': check_early_bird,
        'streak_7': check_streak_7,
        'small_spender': check_small_spender,
        'big_spender': check_big_spender,
        'monthly_champ': check_monthly_champ
    }
    
    for key, check_func in checks.items():
        if not existing.get(key, {}).get('unlocked', 0):
            if check_func():
                unlock_achievement(key)
                newly_unlocked.append(ACHIEVEMENTS[key]['name'])
    
    return newly_unlocked
