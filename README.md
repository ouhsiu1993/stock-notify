# LINE 投資組合機器人

這是一個LINE機器人，用於監控投資組合，提供股票警戒價通知和投資配置建議。

## 功能特色

- 監控多種投資工具：核心ETF、高成長股、波段操作、主題型ETF和高股息ETF
- 自動檢查股票價格是否觸發警戒價，並推送通知
- 提供投資組合狀態報表和再平衡建議
- 定時發送投資組合摘要
- 支援台股和美股查詢

## 使用說明

在LINE聊天中，可以使用以下指令：

- `投資組合` - 查看目前資產配置
- `報表` - 生成詳細配置報表與建議
- `檢查警戒` - 檢查所有股票是否觸發警戒價
- `查詢 [股票代碼]` - 查詢特定股票現價
- `幫助` - 顯示可用指令

## 部署指南

### 事前準備

1. 建立LINE Business帳號並獲取Channel Secret和Channel Access Token
2. 在Render.com註冊帳號

### Render部署步驟

1. 在Render上建立新的Web Service
2. 連接你的GitHub倉庫
3. 設定以下環境變數：
   - `LINE_CHANNEL_SECRET` - LINE Bot的Channel Secret
   - `LINE_CHANNEL_ACCESS_TOKEN` - LINE Bot的Channel Access Token
   - `LINE_USER_ID` - 你的LINE用戶ID
4. 部署後，將Render提供的URL設定為LINE Bot的Webhook URL，格式為: `https://你的域名/callback`

### 重要檔案說明

- `app.py` - 主程式檔案，包含Flask應用和LINE Bot邏輯
- `stocks.json` - 投資組合設定檔案
- `requirements.txt` - 必要的Python套件
- `render.yaml` - Render部署設定
- `Procfile` - 指定應用啟動命令

### 排除常見部署問題

如果遇到 "ModuleNotFoundError: No module named 'app'" 錯誤：
1. 確保 Procfile 中的啟動命令與主程式檔案名稱一致
2. 在Render的"Start Command"欄位直接指定 `gunicorn app:app`
3. 確認主程式中的Flask應用變數名稱是 `app`

如果LINE無法接收訊息：
1. 確認環境變數是否正確設定
2. 檢查LINE Webhook URL是否正確配置
3. 確保LINE Bot已開啟Webhook功能
4. 查看Render日誌以了解可能的錯誤

如果排程任務不執行：
1. 訪問 `/start-scheduler` 路由手動啟動排程
2. 檢查日誌輸出以了解可能的錯誤

### 本地開發

1. 安裝所需套件: `pip install -r requirements.txt`
2. 設定環境變數或創建`.env`文件
3. 啟動應用: `python app.py`
4. 使用ngrok等工具創建臨時公開URL: `ngrok http 5000`
5. 將ngrok提供的URL設定為LINE Bot的Webhook URL

## 自定義投資組合

編輯`stocks.json`文件，可以自訂：

- 投資類別和股票
- 目標配置和現有配置
- 警戒價格和相應行動
- 預期收益率
- 檢查頻率和通知時間

## 安全注意事項

- 請勿將包含敏感資訊的`.env`文件提交到公開倉庫
- 使用`.env.example`作為模板，僅列出所需環境變數名稱，不包含實際值
- 在Render上手動設定所有環境變數
- 將`.env`加入`.gitignore`文件中，確保不會被版本控制追蹤

## 技術架構

- 後端: Python, Flask
- LINE Bot API: line-bot-sdk
- 股票資料: twstock (台股)
- 部署: Render.com

提供的URL設定為LINE Bot的Webhook URL

## 自定義投資組合

編輯`stocks.json`文件，可以自訂：

- 投資類別和股票
- 目標配置和現有配置
- 警戒價格和相應行動
- 預期收益率
- 檢查頻率和通知時間

## 技術架構

- 後端: Python, Flask
- LINE Bot API: line-bot-sdk
- 股票資料: twstock (台股)
- 部署: Render.com