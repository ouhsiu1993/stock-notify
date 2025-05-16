import os
import json
import time
import logging
from datetime import datetime
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    FlexSendMessage, TemplateSendMessage, CarouselTemplate, 
    CarouselColumn, URIAction, MessageAction, 
    BubbleContainer, BoxComponent, TextComponent
)
import twstock
from dotenv import load_dotenv

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 載入環境變數
load_dotenv()

# LINE Bot 設定
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_USER_ID = os.getenv('LINE_USER_ID')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

app = Flask(__name__)

# 載入股票資料
def load_portfolio():
    try:
        with open('stocks.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"載入股票資料失敗: {e}")
        return {"portfolio": {}, "portfolio_summary": {}, "monitoring_rules": {}}

# 取得股票即時資料
def get_stock_price(stock_id):
    try:
        # 台股使用 twstock
        if stock_id.isdigit():
            data = twstock.realtime.get(stock_id)
            if data['success']:
                return float(data['realtime']['latest_trade_price'])
        # 美股使用另外的 API
        else:
            # 這裡用簡單的示例，實際應用需要整合美股API
            # 例如: Alpha Vantage, Yahoo Finance 等
            # 假設我們有一個取得美股價格的函數
            return get_us_stock_price(stock_id)
    except Exception as e:
        logger.error(f"獲取股票 {stock_id} 價格失敗: {e}")
    return None

# 模擬美股API (實際使用時需替換為真實API)
def get_us_stock_price(stock_id):
    # 這裡只是示範，實際應用需整合真實API
    mock_prices = {
        'NVDA': 4156.75
    }
    return mock_prices.get(stock_id, 0)

# 發送Line訊息
def send_line_message(text):
    try:
        line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=text))
        logger.info(f"成功發送訊息: {text}")
        return True
    except Exception as e:
        logger.error(f"發送訊息失敗: {e}")
        return False

# 發送投資組合狀態
def send_portfolio_status():
    portfolio_data = load_portfolio()
    summary = portfolio_data.get('portfolio_summary', {})
    
    total_value = summary.get('total_value', 0)
    message = f"📊 投資組合總值: ${total_value:,}\n\n"
    
    for category, stocks in portfolio_data.get('portfolio', {}).items():
        message += f"【{category}】\n"
        for stock in stocks:
            current_price = get_stock_price(stock['id']) or stock['current_price']
            current_value = current_price * stock['quantity']
            message += f"- {stock['name']} ({stock['id']}): {current_price} 元 x {stock['quantity']} = ${current_value:,.0f}\n"
        message += "\n"
    
    send_line_message(message)

# 檢查股票是否觸發警戒價
def check_stock_alerts():
    portfolio_data = load_portfolio()
    alerts = []
    
    for category, stocks in portfolio_data.get('portfolio', {}).items():
        for stock in stocks:
            current_price = get_stock_price(stock['id'])
            if current_price:
                # 檢查是否低於下限
                if stock.get('threshold_down') and current_price <= stock['threshold_down']:
                    alerts.append(f"⚠️ {stock['name']} ({stock['id']}) 現價 {current_price} 元，低於警戒價 {stock['threshold_down']} 元!\n建議行動: {stock['action_down']}")
                
                # 檢查是否高於上限
                if stock.get('threshold_up') and current_price >= stock['threshold_up']:
                    alerts.append(f"🔔 {stock['name']} ({stock['id']}) 現價 {current_price} 元，高於警戒價 {stock['threshold_up']} 元!\n建議行動: {stock['action_up']}")
    
    if alerts:
        send_line_message("\n\n".join(alerts))

# 生成投資組合報表
def generate_portfolio_report():
    portfolio_data = load_portfolio()
    summary = portfolio_data.get('portfolio_summary', {})
    
    total_value = 0
    target_value = summary.get('target_value', 0)
    report = "📈 投資組合配置報表 📈\n\n"
    
    for category, stocks in portfolio_data.get('portfolio', {}).items():
        category_value = 0
        report += f"【{category}】\n"
        
        for stock in stocks:
            current_price = get_stock_price(stock['id']) or stock['current_price']
            current_value = current_price * stock['quantity']
            category_value += current_value
            
            # 計算與目標的差距
            target_diff = stock['target_quantity'] - stock['quantity']
            target_action = "買入" if target_diff > 0 else "賣出"
            target_diff_abs = abs(target_diff)
            
            # 只有當數量差距不為0時才顯示建議
            if target_diff != 0:
                report += f"- {stock['name']} ({stock['id']}): 現價 {current_price} 元\n  持有 {stock['quantity']}，目標 {stock['target_quantity']}，建議{target_action} {target_diff_abs}\n"
            else:
                report += f"- {stock['name']} ({stock['id']}): 現價 {current_price} 元\n  持有 {stock['quantity']}，已達目標數量\n"
        
        total_value += category_value
        report += f"  小計: ${category_value:,.0f}\n\n"
    
    # 總結
    report += f"總資產: ${total_value:,.0f}\n"
    report += f"目標資產: ${target_value:,.0f}\n"
    
    # 計算與總目標的差距百分比
    diff_percent = ((total_value - target_value) / target_value * 100) if target_value else 0
    report += f"差距: {diff_percent:.1f}%\n"
    
    return report

# LINE Bot webhook
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.strip()
    
    if text == '投資組合':
        send_portfolio_status()
    
    elif text == '報表':
        report = generate_portfolio_report()
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=report))
    
    elif text == '檢查警戒':
        check_stock_alerts()
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="已檢查所有股票警戒價，若有觸發會另行通知"))
    
    elif text.startswith('查詢 ') or text.startswith('查詢'):
        stock_id = text.replace('查詢', '').strip()
        price = get_stock_price(stock_id)
        if price:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"{stock_id} 現價: {price} 元"))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"無法獲取 {stock_id} 的價格"))
    
    elif text == '幫助':
        help_text = (
            "📱 投資組合機器人使用指南:\n\n"
            "• 投資組合 - 查看目前資產配置\n"
            "• 報表 - 生成詳細配置報表與建議\n"
            "• 檢查警戒 - 檢查所有股票是否觸發警戒價\n"
            "• 查詢 [股票代碼] - 查詢特定股票現價\n"
            "• 幫助 - 顯示此幫助信息"
        )
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=help_text))
    
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="我不明白您的指令，請輸入「幫助」查看可用指令"))

# 定時任務
def scheduled_tasks():
    current_time = datetime.now().strftime('%H:%M')
    portfolio_data = load_portfolio()
    notification_times = portfolio_data.get('monitoring_rules', {}).get('notification_time', [])
    
    # 如果當前時間在通知時間列表中，發送投資組合狀態
    if current_time in notification_times:
        send_portfolio_status()
    
    # 檢查股票警戒價
    check_stock_alerts()

# 主程序
if __name__ == "__main__":
    # 啟動排程器
    import threading
    def run_scheduler():
        while True:
            try:
                scheduled_tasks()
            except Exception as e:
                logger.error(f"排程任務執行失敗: {e}")
            # 每小時檢查一次
            time.sleep(3600)
    
    # 啟動排程器線程
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    
    # 啟動 Flask 應用
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)