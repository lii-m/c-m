"""
AI财务分析模块 - 元气记账本
调用DeepSeek API生成毒舌可爱的财务分析
"""

import os
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime, timedelta
from db_helper import get_expenses

# 加载环境变量（本地开发）
load_dotenv()

# 优先从 Streamlit Secrets 获取，其次从环境变量获取
try:
    import streamlit as st
    API_KEY = st.secrets.get('DEEPSEEK_API_KEY', os.getenv('DEEPSEEK_API_KEY'))
except:
    API_KEY = os.getenv('DEEPSEEK_API_KEY')


def analyze_spending(user_id=None):
    """
    分析最近7天的消费记录，调用DeepSeek API生成吐槽和建议
    返回：{ 'tucao': str, 'suggestions': [str, str, str], 'insight': str }
    """
    if not API_KEY:
        return {
            'tucao': '哎呀，API Key还没配置好呢，先去设置一下吧~',
            'suggestions': ['配置DeepSeek API Key', '添加一些消费记录', '再来分析~'],
            'insight': '没有API Key，本元宝也无能为力呀！'
        }
    
    # 获取最近7天记录
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    all_expenses = get_expenses(user_id)
    # 过滤只显示支出
    all_expenses = [e for e in all_expenses if len(e) > 8 and e[8] == 0]
    recent = [e for e in all_expenses 
              if start_date <= datetime.strptime(e[2], '%Y-%m-%d') <= end_date]
    
    if not recent:
        return {
            'tucao': '最近7天一条记录都没有，你是把钱包封印了吗？',
            'suggestions': ['记账是个好习惯', '哪怕花1块钱也记下来', '坚持7天就有惊喜'],
            'insight': '没有数据就没有发言权，快去买点东西记账吧！'
        }
    
    # 整理消费数据文本
    lines = []
    total = 0
    for e in recent:
        lines.append(f"{e[2]} 花了{e[3]}元买{e[4]}（{e[5] or '无子分类'}），感觉{e[6]}")
        total += e[3]
    
    expense_text = "\n".join(lines)
    
    # 构建Prompt
    prompt = f"""你是元宝，一个毒舌但可爱的女性财务助手。请根据以下最近7天的消费记录，给出吐槽和分析。

【消费记录】
{expense_text}

【要求】
请用JSON格式返回，包含以下三个字段：
1. "tucao": 一句毒舌吐槽（可爱风格，带emoji）
2. "suggestions": 三个具体省钱建议（数组）
3. "insight": 一个情绪消费洞察（发现消费和情绪的关系）

注意：
- 语气要毒舌但可爱，像闺蜜聊天
- 吐槽要一针见血
- 建议要实用具体
- 洞察要有深度
- 必须用严格的JSON格式返回
"""
    
    try:
        client = OpenAI(
            api_key=API_KEY,
            base_url="https://api.deepseek.com/v1"
        )
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是元宝，一个毒舌但可爱的女性财务助手。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=500
        )
        
        content = response.choices[0].message.content
        
        # 尝试解析JSON
        import json
        # 清理可能的markdown代码块标记
        if '```' in content:
            content = content.split('```')[1].replace('json', '').strip()
        
        result = json.loads(content)
        return {
            'tucao': result.get('tucao', '吐槽生成失败...'),
            'suggestions': result.get('suggestions', ['建议1', '建议2', '建议3']),
            'insight': result.get('insight', '洞察生成失败...')
        }
        
    except Exception as e:
        return {
            'tucao': f'API调用出问题了：{str(e)[:50]}',
            'suggestions': ['检查网络连接', '确认API Key有效', '稍后再试'],
            'insight': '技术故障，元宝暂时下线中...'
        }
