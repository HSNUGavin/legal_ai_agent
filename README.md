# Legal AI Agent

法律案例分析 AI 助手，能夠自動分析判決書並提供相關案例參考。

## 功能特點

- 多輪對話支援：AI 能夠進行深度的案例分析，並保持對話上下文
- 自動案例搜索：根據關鍵詞自動搜索相關判決
- 數據分析：提供量化的判決統計分析
- 即時互動：使用 WebSocket 實現即時對話
- 支援多個對話：可以同時進行多個獨立的案例分析對話

## 系統需求

- Python 3.11+
- Node.js 16+
- SQLite3

## 快速開始

1. 安裝後端依賴：
```bash
pip install -r requirements.txt
```

2. 設定環境變數：
創建 `.env` 文件並設定：
```
OPENAI_API_KEY=你的OpenAI API金鑰
```

3. 安裝前端依賴：
```bash
cd frontend
npm install
```

4. 建置前端：
```bash
cd frontend
npm run build
```

5. 啟動服務器：
```bash
python -m uvicorn app:app --reload
```

6. 開啟瀏覽器訪問：
```
http://localhost:8000
```

## 專案結構

- `app.py`: FastAPI 後端服務器
- `agent.py`: AI 代理核心邏輯
- `config.py`: 配置文件
- `frontend/`: React 前端代碼
- `files/`: 數據文件目錄
- `history/`: 對話歷史記錄

## 資料庫說明

系統使用三個主要資料表：

1. `judgement_guilty_analysis_grouping`: 判決統計分析
2. `judgement_raw`: 原始判決書內容
3. `judgements_guilty_analysis_by_row`: 詳細案件分析

## API 文檔

### WebSocket 端點

- `/ws/{conversation_id}`: 建立 WebSocket 連接進行對話

### REST API

- `GET /api/conversations`: 列出所有對話
- `POST /api/conversations`: 創建新對話

## 開發說明

1. 前端開發：
```bash
cd frontend
npm run dev
```

2. 後端開發：
```bash
python -m uvicorn app:app --reload
```

## 注意事項

- 請確保 `files/` 目錄中有必要的數據文件
- 首次運行時會自動創建必要的目錄和數據庫
- 對話歷史會自動保存在 `history/` 目錄中
