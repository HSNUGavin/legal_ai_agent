from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import json
from agent import Agent
import re
import os
import asyncio
from typing import Dict, Optional
from pydantic import BaseModel

app = FastAPI()

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite 默認端口
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 存儲每個連接的處理任務和代理
processing_tasks: Dict[WebSocket, asyncio.Task] = {}
active_agents: Dict[str, Agent] = {}

async def process_message(websocket: WebSocket, message: dict, agent: Agent):
    """處理用戶消息的異步函數"""
    try:
        # 獲取 AI 回應
        response = agent.think(message["content"])
        while True:
            processed_response = process_ai_response(agent, response, message["content"])
            await websocket.send_json({
                "role": "assistant",
                "content": processed_response
            })
            if processed_response == response:  # 如果回應沒有改變，說明不需要繼續處理
                break
            response = processed_response
    except asyncio.CancelledError:
        await websocket.send_json({
            "type": "status",
            "content": "done"
        })
        raise
    except Exception as e:
        print(f"處理消息時出錯: {e}")
        await websocket.send_json({
            "role": "assistant",
            "content": f"處理過程中出現錯誤: {str(e)}"
        })

def process_ai_response(agent, response, initial_input=None):
    """處理 AI 的回應，包括執行動作和處理結果"""
    # 檢查 AI 的動作
    if match := re.search(r'<action>READ_FILE (.*?)</action>', response):
        filename = match.group(1)
        file_content = agent.read_file(filename)
        
        # 讓 AI 處理文件內容
        return agent.think(f"我已經讀取了文件 {filename}，內容如下:\n{file_content}")
    
    elif match := re.search(r'<action>SQL (.*?)</action>', response):
        sql = match.group(1)
        result = agent.execute_sql(sql)
        
        # 讓 AI 處理 SQL 結果
        return agent.think(f"SQL 查詢結果如下:\n{result}")
    
    # 檢查是否繼續
    if match := re.search(r'<if_finish>(.*?)</if_finish>', response):
        decision = match.group(1).strip().lower()
        if decision == 'continue':
            next_input = initial_input if initial_input else "請繼續分析上述情況。"
            return agent.think(next_input)
    
    return response

# WebSocket 連接處理
@app.websocket("/ws/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: str):
    await websocket.accept()
    
    # 獲取或創建 Agent
    if conversation_id not in active_agents:
        active_agents[conversation_id] = Agent(conversation_id)
    agent = active_agents[conversation_id]
    current_task = None
    
    try:
        # 發送歷史消息
        if agent.conversation_history:
            await websocket.send_json({
                "type": "history",
                "content": agent.conversation_history
            })
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # 處理中止請求
            if message.get("type") == "stop":
                if current_task and not current_task.done():
                    current_task.cancel()
                    await websocket.send_json({
                        "type": "status",
                        "content": "done"
                    })
                continue
            
            # 回傳用戶的訊息
            await websocket.send_json({
                "role": "user",
                "content": message["content"]
            })
            
            # 取消之前的任務（如果存在）
            if current_task and not current_task.done():
                current_task.cancel()
                try:
                    await current_task
                except asyncio.CancelledError:
                    pass
            
            # 創建新的處理任務
            current_task = asyncio.create_task(
                process_message(websocket, message, agent)
            )
            processing_tasks[websocket] = current_task
            
            try:
                await current_task
            except asyncio.CancelledError:
                pass
                
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        if websocket in processing_tasks:
            task = processing_tasks[websocket]
            if not task.done():
                task.cancel()
            del processing_tasks[websocket]
        await websocket.close()

# API 路由
@app.get("/api/conversations")
async def list_conversations():
    """列出所有可用的對話"""
    return Agent.list_conversations()

@app.post("/api/conversations")
async def create_conversation():
    """創建新對話"""
    agent = Agent()  # 會自動生成新的 conversation_id
    active_agents[agent.conversation_id] = agent
    return {
        "id": agent.conversation_id,
        "last_update": "",
        "messages_count": 0
    }

# 根路由處理
@app.get("/")
async def read_root():
    return FileResponse('frontend/dist/index.html')

# 提供其他靜態文件
app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="static")
