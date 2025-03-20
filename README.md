# 法律 AI 助手

一個基於 Python 後端和 React 前端的法律 AI 助手系統，用於分析法律案例並提供法律建議。

## 功能特點

- 使用 OpenAI GPT-4o 模型進行法律分析
- 互動式 Web 介面，顯示 AI 思考過程
- 支援 SQL 查詢和文件讀取
- 即時顯示 AI 思考步驟的流程圖
- 對話歷史記錄和重置功能

## 系統架構

- **後端**：Flask API + OpenAI
- **前端**：React + ReactFlow
- **資料庫**：SQLite (自動從 CSV 文件導入)

## 安裝步驟

1. 安裝必要的 Python 套件：

```bash
pip install -r requirements.txt
```

2. 設置環境變數：

創建 `.env` 文件並添加您的 OpenAI API 密鑰：

```
OPENAI_API_KEY=your_api_key_here
```

## 運行應用

1. 啟動 Flask API 伺服器：

```bash
python api.py
```

2. 在瀏覽器中打開前端頁面：

```
frontend/index.html
```

## 使用方法

1. 在輸入框中輸入您的法律問題
2. AI 會在右側面板顯示思考過程
3. 最終回應會顯示在對話框中
4. 點擊「重置對話」按鈕可以開始新的對話

## 系統流程

1. 用戶輸入問題
2. AI 分析問題並顯示思考過程
3. AI 可能執行 SQL 查詢或讀取文件
4. 最終生成回應並顯示給用戶
