# 法律 AI 助手

一個基於 Python 後端和 React 前端的法律 AI 助手系統，用於分析法律案例並提供法律建議。

> [English version](./README_EN.md)

## 功能特點

- 使用 OpenAI GPT-4o 模型進行法律分析
- 互動式 Web 介面，顯示 AI 思考過程
- 支援 SQL 查詢和文件讀取
- 即時顯示 AI 思考步驟的流程圖
- 對話歷史記錄和重置功能
- 支援 Markdown 格式化文本顯示
- 優化的用戶界面，清晰分離思考過程和最終回應
- 多代理協作工作流程，提高分析質量

## 系統架構

- **後端**：Flask API + OpenAI
- **前端**：React + ReactFlow + Marked.js
- **資料庫**：SQLite (自動從 CSV 文件導入)
- **代理系統**：多階段代理工作流程 (規劃、控制、分析、總結)

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
http://localhost:5000
```

## 使用方法

1. 在輸入框中輸入您的法律問題
2. AI 會在右側面板顯示思考過程
3. 最終回應會顯示在對話框中，支援 Markdown 格式
4. 點擊「重置對話」按鈕可以開始新的對話

## 系統流程

1. 用戶輸入問題
2. 規劃代理分析問題並制定策略
3. 控制代理協調任務執行
4. 分析/搜索代理執行具體任務（如 SQL 查詢或文件讀取）
5. 總結代理生成最終回應並顯示給用戶

## 技術細節

- 使用特殊標籤 (`<think>`, `<action>`, `<content>`, `<if_finish>`) 處理 AI 回應
- 右側面板顯示思考步驟和執行動作
- 對話欄僅顯示最終清理後的內容
- 支援 Markdown 格式，包括代碼塊、表格、列表等
