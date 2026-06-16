"""
元气记账本 - 主程序
情绪+游戏化+AI智能记账助手
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

from db_helper import (
    add_expense, get_expenses, get_expenses_by_date_range,
    get_monthly_expenses, get_total_monthly_expense,
    get_most_expensive, get_daily_expense, get_setting, set_setting
)
from game_logic import (
    calculate_budget_progress, get_pet_mood,
    check_all_achievements, ACHIEVEMENTS, get_monthly_summary
)
from ai_advisor import analyze_spending

# ========== 页面配置 ==========
st.set_page_config(
    page_title="元气记账本",
    page_icon="🐱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== 消费分类配置 ==========
CATEGORIES = {
    "餐饮": ["三餐", "奶茶咖啡", "零食", "外卖", "聚餐"],
    "购物": ["衣服", "数码", "美妆", "书籍", "日用"],
    "娱乐": ["游戏", "电影", "音乐", "聚会"],
    "交通": ["公交地铁", "打车", "加油", "共享单车"],
    "住宿": ["房租", "水电", "网费", "家具"],
    "学习": ["课程", "资料", "打印"],
    "医疗": ["药品", "挂号", "体检"],
    "社交": ["送礼", "请客"],
    "宠物": ["粮", "玩具", "医疗"],
    "其他": []
}

EMOTIONS = {
    "😊开心": 5,
    "🥰幸福": 4,
    "😐平静": 3,
    "😡暴躁": 2,
    "😔后悔": 1
}

# ========== 主题配置 ==========
THEMES = {
    'female': {
        'name': '女生版',
        'icon': '👧',
        'bg': '#FFF8F0',
        'primary': '#FF69B4',
        'secondary': '#FFB6C1',
        'border': '#FFE4E1',
        'btn_gradient': 'linear-gradient(135deg, #FFB6C1 0%, #FF69B4 100%)',
        'progress': 'linear-gradient(90deg, #FFB6C1 0%, #FF69B4 100%)'
    },
    'male': {
        'name': '男生版',
        'icon': '👦',
        'bg': '#E8F4FD',
        'primary': '#4169E1',
        'secondary': '#87CEEB',
        'border': '#B8E4F0',
        'btn_gradient': 'linear-gradient(135deg, #87CEEB 0%, #4169E1 100%)',
        'progress': 'linear-gradient(90deg, #87CEEB 0%, #4169E1 100%)'
    }
}

# ========== CSS样式 ==========
def get_theme():
    return THEMES.get(st.session_state.get('theme', 'female'), THEMES['female'])

def render_css():
    theme = get_theme()
    css = f"""
    <style>
    body {{ background: {theme['bg']}; }}
    .stButton > button {{
        background: {theme['btn_gradient']};
        color: white;
        border: none;
        border-radius: 20px;
        padding: 10px 24px;
        font-weight: 600;
    }}
    .stProgress > div > div > div {{
        background: {theme['progress']};
        border-radius: 10px;
    }}
    h1, h2, h3, h4, h5, h6 {{
        color: {theme['primary']};
        font-family: 'Microsoft YaHei', sans-serif;
    }}
    
    /* ===== 美化标签页 ===== */
    .stTabs {{
        margin-bottom: 1rem;
    }}
    
    .stTabs [role="tablist"] {{
        gap: 10px;
        justify-content: center;
        padding: 10px 0;
    }}
    
    /* 默认状态：杏色渐变 */
    .stTabs [role="tab"] {{
        background: linear-gradient(145deg, #FFEFD5 0%, #F5DEB3 100%);
        border: 1.5px solid #DEB887;
        border-radius: 12px;
        padding: 12px 24px;
        font-size: 18px;
        font-weight: 600;
        color: #8B4513;
        transition: all 0.3s ease;
        min-width: 120px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(210, 180, 140, 0.2);
    }}
    
    .stTabs [role="tab"]:hover {{
        background: linear-gradient(145deg, #FFF8DC 0%, #FFEFD5 100%);
        border-color: #D2691E;
        color: #8B4513;
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(210, 105, 30, 0.3);
    }}
    
    .stTabs [role="tab"][aria-selected="true"] {{
        background: linear-gradient(145deg, #FFE0B2 0%, #FFCC80 100%);
        border-color: #FF9800;
        color: #E65100;
        box-shadow: 0 4px 15px rgba(255, 152, 0, 0.4);
    }}
    
    /* 每个标签页不同的渐变色 */
    .stTabs [role="tab"]:nth-child(1)[aria-selected="true"] {{
        background: linear-gradient(145deg, #E3F2FD 0%, #BBDEFB 100%);
        border-color: #64B5F6;
        color: #1976D2;
        box-shadow: 0 4px 15px rgba(100, 181, 246, 0.4);
    }}
    
    .stTabs [role="tab"]:nth-child(2)[aria-selected="true"] {{
        background: linear-gradient(145deg, #FCE4EC 0%, #F8BBD9 100%);
        border-color: #F48FB1;
        color: #C2185B;
        box-shadow: 0 4px 15px rgba(244, 143, 177, 0.4);
    }}
    
    .stTabs [role="tab"]:nth-child(3)[aria-selected="true"] {{
        background: linear-gradient(145deg, #E8F5E9 0%, #C8E6C9 100%);
        border-color: #81C784;
        color: #2E7D32;
        box-shadow: 0 4px 15px rgba(129, 199, 132, 0.4);
    }}
    
    .stTabs [role="tab"]:nth-child(4)[aria-selected="true"] {{
        background: linear-gradient(145deg, #EDE7F6 0%, #D1C4E9 100%);
        border-color: #BA68C8;
        color: #6A1B9A;
        box-shadow: 0 4px 15px rgba(186, 104, 200, 0.4);
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# ========== 侧边栏 ==========
def sidebar():
    with st.sidebar:
        # 主题切换
        theme_key = st.selectbox(
            "选择主题",
            options=['female', 'male'],
            format_func=lambda x: f"{THEMES[x]['icon']} {THEMES[x]['name']}",
            key='theme'
        )
        theme = THEMES[theme_key]
        
        st.markdown(f"<h2 style='text-align:center;color:{theme['primary']}'>🐱 元气记账本</h2>", unsafe_allow_html=True)
        
        # 宠物小猫
        mood, emoji = get_pet_mood()
        st.markdown(f"<div style='text-align:center;font-size:60px'>{emoji}</div>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center;color:{theme['primary']}'>小猫心情：{mood}</p>", unsafe_allow_html=True)
        
        # 本月总花费
        now = datetime.now()
        total = get_total_monthly_expense(now.year, now.month)
        st.markdown(f"<p style='color:#888;font-size:14px'>本月总花费</p><p style='font-size:28px;font-weight:bold;color:{theme['primary']}'>¥{total:.2f}</p>", unsafe_allow_html=True)
        
        # 预算进度
        bp = calculate_budget_progress()
        st.markdown("<p style='color:#888;font-size:14px'>预算进度</p>", unsafe_allow_html=True)
        if bp['over_budget']:
            st.markdown("<p style='color:#FF4444;font-size:12px'>⚠️ 超预算啦！</p>", unsafe_allow_html=True)
        st.progress(bp['progress'])
        st.markdown(f"<p style='text-align:center;color:#888;font-size:12px'>剩余 ¥{bp['remaining']:.2f}</p>", unsafe_allow_html=True)
        
        # 今日花费
        today = now.strftime('%Y-%m-%d')
        today_expense = get_daily_expense(today)
        st.markdown(f"<p style='color:#888;font-size:14px'>今日花费</p><p style='font-size:20px;font-weight:bold;color:{theme['primary']}'>¥{today_expense:.2f}</p>", unsafe_allow_html=True)
        
        # 最贵一笔
        most = get_most_expensive(now.year, now.month)
        if most:
            st.markdown(f"<p style='color:#888;font-size:14px'>本月最贵</p><p style='font-size:16px;color:#FF69B4'>¥{most[2]:.2f} - {most[3]}</p>", unsafe_allow_html=True)

# ========== 记账页面 ==========
def page_expense():
    st.markdown("<h2>📝 记一笔</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("<div style='background:rgba(255,255,255,0.95);border-radius:20px;padding:20px;box-shadow:0 4px 15px rgba(0,0,0,0.08)'>", unsafe_allow_html=True)
        
        date = st.date_input("日期", datetime.now())
        amount = st.number_input("金额", min_value=0.0, step=0.1, format="%.2f")
        category = st.selectbox("一级分类", list(CATEGORIES.keys()))
        subcategory = st.selectbox("二级分类", CATEGORIES[category]) if CATEGORIES[category] else None
        emotion = st.selectbox("情绪标签", list(EMOTIONS.keys()))
        
        custom = st.text_area("备注", height=60, placeholder="在这里输入备注...")
        note = custom if custom else None
        
        if st.button("💾 保存记录"):
            if amount <= 0:
                st.toast("金额必须大于0！", icon="⚠️")
            else:
                add_expense(
                    date.strftime('%Y-%m-%d'),
                    amount, category,
                    subcategory if subcategory else None,
                    emotion, note if note else None
                )
                unlocked = check_all_achievements()
                for a in unlocked:
                    st.toast(f"🎉 解锁成就：{a}！", icon="🏆")
                st.toast("✅ 记账成功！", icon="💰")
                st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # 历史记录区域
    with col2:
        st.markdown("<h3>📋 消费记录</h3>", unsafe_allow_html=True)
        
        now = datetime.now()
        c1, c2, c3 = st.columns(3)
        with c1:
            sel_year = st.selectbox("年份", range(2020, now.year + 1), index=now.year - 2020)
        with c2:
            sel_month = st.selectbox("月份", range(1, 13), index=now.month - 1)
        with c3:
            show_all = st.checkbox("查看整月", value=True)
            if not show_all:
                sel_day = st.slider("日期", 1, 31, now.day)
        
        # 筛选记录
        if show_all:
            filtered = get_monthly_expenses(sel_year, sel_month)
        else:
            expenses = get_monthly_expenses(sel_year, sel_month)
            target = f"{sel_year}-{sel_month:02d}-{sel_day:02d}"
            filtered = [e for e in expenses if e[1] == target]
        
        # 折叠展示
        show_all_rec = st.session_state.get('show_all_records', False)
        limit = len(filtered) if show_all_rec else 5
        
        if filtered:
            df = pd.DataFrame(filtered, columns=['ID', '日期', '金额', '分类', '子分类', '情绪', '备注', '创建时间'])
            df.insert(0, '序号', range(1, len(df) + 1))
            df = df[['序号', '日期', '金额', '分类', '子分类', '情绪', '备注']]
            df['金额'] = df['金额'].apply(lambda x: f"¥{x:.2f}")
            
            st.dataframe(df.head(limit), use_container_width=True)
            
            if len(filtered) > 5:
                if not show_all_rec:
                    if st.button("🔍 查看更多"):
                        st.session_state['show_all_records'] = True
                        st.rerun()
                else:
                    if st.button("📦 收起"):
                        st.session_state['show_all_records'] = False
                        st.rerun()
        else:
            st.markdown("<p style='text-align:center;color:#888'>该时间段没有消费记录~</p>", unsafe_allow_html=True)

# ========== 情绪账本页面 ==========
def page_emotion():
    st.markdown("<h2>📊 情绪账本</h2>", unsafe_allow_html=True)
    
    expenses = get_expenses()
    if not expenses:
        st.info("还没有消费记录，快去记一笔吧！")
        return
    
    df = pd.DataFrame(expenses, columns=['ID', '日期', '金额', '分类', '子分类', '情绪', '备注', '创建时间'])
    df['情绪分值'] = df['情绪'].map(EMOTIONS)
    df['情绪颜色'] = df['情绪'].map({
        "😊开心": "#FFF5E6",
        "🥰幸福": "#FFE4EC",
        "😐平静": "#E6F7FF",
        "😡暴躁": "#FFE4E1",
        "😔后悔": "#F5E6FF"
    })
    
    # 情绪消费散点图
    col1, col2 = st.columns(2)
    with col1:
        fig1 = px.scatter(df, x='金额', y='情绪分值', color='情绪',
                         color_discrete_map={
                             "😊开心": "#FFD4A3",
                             "🥰幸福": "#FFB8D0",
                             "😐平静": "#B8E6FF",
                             "😡暴躁": "#FFB3AD",
                             "😔后悔": "#E8C8FF"
                         },
                         title="消费金额 vs 情绪分值")
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # 各分类平均情绪
        cat_emotion = df.groupby('分类')['情绪分值'].mean().reset_index()
        fig2 = px.bar(cat_emotion, x='分类', y='情绪分值',
                      title="各分类平均情绪分值",
                      color='情绪分值',
                      color_continuous_scale=['#FFE4EC', '#FFD4A3', '#B8E6FF', '#A8E6CF', '#FFB8D0'])
        st.plotly_chart(fig2, use_container_width=True)
    
    # 情绪消费报告
    st.markdown("<h3>📋 情绪消费报告</h3>", unsafe_allow_html=True)
    
    # 最开心消费
    happy = df[df['情绪'].isin(['😊开心', '🥰幸福'])]
    if not happy.empty:
        happiest = happy.groupby('分类')['金额'].sum().idxmax()
        st.markdown(f"<div style='background:linear-gradient(135deg,#FFE4E1 0%,#FFB6C1 100%);border-radius:12px;padding:15px'><p style='color:#FF69B4;font-weight:bold'>😊 最让你开心的消费类别：{happiest}</p></div>", unsafe_allow_html=True)
    
    # 最后悔消费
    regret = df[df['情绪'] == '😔后悔']
    if not regret.empty:
        most_regret = regret.groupby('分类')['金额'].sum().idxmax()
        st.markdown(f"<div style='background:linear-gradient(135deg,#FFE4E4 0%,#FFB6B6 100%);border-radius:12px;padding:15px;margin-top:10px'><p style='color:#CD5C5C;font-weight:bold'>😔 最容易后悔的消费类别：{most_regret}</p></div>", unsafe_allow_html=True)

# ========== 成就页面 ==========
def page_achievements():
    st.markdown("<h2>🎮 我的成就</h2>", unsafe_allow_html=True)
    
    # 预算设置
    st.markdown("<h3>💰 月度预算</h3>", unsafe_allow_html=True)
    current_budget = float(get_setting('monthly_budget') or 2000)
    new_budget = st.number_input("设置月预算", min_value=100, value=int(current_budget), step=100)
    if new_budget != current_budget:
        set_setting('monthly_budget', new_budget)
        st.toast("预算已更新！", icon="✅")
        st.rerun()
    
    # 预算进度
    bp = calculate_budget_progress()
    st.progress(bp['progress'])
    st.markdown(f"**已用：** ¥{bp['total']:.2f} / **预算：** ¥{bp['budget']:.2f}")
    if bp['over_budget']:
        st.error("⚠️ 已超预算！要克制一下啦！")
    
    # 成就展示
    st.markdown("## 成就徽章")
    from game_logic import get_all_achievements
    unlocked = get_all_achievements()
    
    # HTML模板 - 使用更稳定的渲染方式
    def render_badge(icon, name, desc, colors):
        bg = colors[0]
        border = colors[1]
        
        html = f"""
        <div style="background:{bg};border:{border};border-radius:12px;padding:15px;margin:5px;text-align:center;min-height:130px;">
            <div style="font-size:42px;margin:5px 0;">{icon}</div>
            <div style="font-weight:bold;font-size:14px;margin:5px 0;">{name}</div>
            <div style="font-size:11px;color:#666;">{desc}</div>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)
    
    # 成就颜色配置
    badge_colors = [
        ("#E8F5E9", "#81C784"),
        ("#E3F2FD", "#64B5F6"),
        ("#FFF3E0", "#FFB74D"),
        ("#FCE4EC", "#F48FB1"),
        ("#EDE7F6", "#BA68C8"),
        ("#E0F7FA", "#4DD0E1"),
        ("#FFF9C4", "#FFD54F"),
        ("#F3E5F5", "#CE93D8"),
        ("#EFEBE9", "#A1887F"),
        ("#ECEFF1", "#90A4AE"),
    ]
    
    achievements_list = list(ACHIEVEMENTS.items())
    
    # 第一排
    cols_row1 = st.columns(5)
    for i in range(5):
        with cols_row1[i]:
            if i < len(achievements_list):
                key, info = achievements_list[i]
                is_unlocked = unlocked.get(key, {}).get('unlocked', 0)
                
                if is_unlocked:
                    render_badge(info['icon'], info['name'], info['desc'], badge_colors[i])
                else:
                    render_badge("🔒", info['name'], info['desc'], ("#F5F5F5", "#DDD"))
    
    # 第二排
    cols_row2 = st.columns(5)
    for i in range(5):
        with cols_row2[i]:
            idx = i + 5
            if idx < len(achievements_list):
                key, info = achievements_list[idx]
                is_unlocked = unlocked.get(key, {}).get('unlocked', 0)
                
                if is_unlocked:
                    render_badge(info['icon'], info['name'], info['desc'], badge_colors[idx])
                else:
                    render_badge("🔒", info['name'], info['desc'], ("#F5F5F5", "#DDD"))

# ========== AI分析页面 ==========
def page_ai():
    st.markdown("<h2>🤖 AI财务分析</h2>", unsafe_allow_html=True)
    
    # 消费概览
    summary = get_monthly_summary()
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"<div style='background:linear-gradient(135deg,#FFE4E1 0%,#FFB6C1 100%);border-radius:12px;padding:20px;text-align:center'><p style='color:#888;font-size:14px'>本月总消费</p><p style='font-size:28px;font-weight:bold;color:#FF69B4'>¥{summary['total']:.2f}</p></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div style='background:linear-gradient(135deg,#E0FFE0 0%,#98FB98 100%);border-radius:12px;padding:20px;text-align:center'><p style='color:#888;font-size:14px'>记录笔数</p><p style='font-size:28px;font-weight:bold;color:#3CB371'>{summary['count']}</p></div>", unsafe_allow_html=True)
    with c3:
        most = max(summary['category_totals'], key=summary['category_totals'].get) if summary['category_totals'] else '暂无'
        st.markdown(f"<div style='background:linear-gradient(135deg,#E6E6FA 0%,#DDA0DD 100%);border-radius:12px;padding:20px;text-align:center'><p style='color:#888;font-size:14px'>最大消费类别</p><p style='font-size:20px;font-weight:bold;color:#9932CC'>{most}</p></div>", unsafe_allow_html=True)
    
    # AI分析按钮
    if st.button("🔮 召唤元宝分析", use_container_width=True):
        with st.spinner("元宝正在分析你的消费记录..."):
            result = analyze_spending()
        
        st.markdown("<div style='background:linear-gradient(135deg,#FFF8F0 0%,#FFE4E1 100%);border-radius:20px;padding:25px;margin-top:20px'>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='color:#FF69B4'>💢 元宝吐槽</h3><p style='font-size:18px'>{result['tucao']}</p>", unsafe_allow_html=True)
        
        st.markdown(f"<h3 style='color:#FF69B4'>💡 省钱建议</h3>", unsafe_allow_html=True)
        for i, s in enumerate(result['suggestions'], 1):
            st.markdown(f"{i}. {s}")
        
        st.markdown(f"<h3 style='color:#FF69B4'>🔍 情绪洞察</h3><p style='font-size:16px'>{result['insight']}</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ========== 主程序入口 ==========
def main():
    render_css()
    sidebar()
    
    tab1, tab2, tab3, tab4 = st.tabs(["📝 记账本", "📊 情绪账本", "🎮 我的成就", "🤖 AI分析"])
    
    with tab1:
        page_expense()
    with tab2:
        page_emotion()
    with tab3:
        page_achievements()
    with tab4:
        page_ai()

if __name__ == "__main__":
    main()
