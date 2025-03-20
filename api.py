from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS
import json
import time
import re
import os
from agent import Agent
from config import HISTORY_FILE  # Import HISTORY_FILE from config

app = Flask(__name__, static_folder='frontend')
CORS(app)  # Enable CORS for all routes

# Initialize the agent
agent = Agent()

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_input = data.get('message', '')
    is_processing = data.get('isProcessing', False)
    
    print("\n=== 收到用戶輸入 ===")
    print(f"用戶輸入: {user_input[:100]}...")
    print(f"是否處理中: {is_processing}")
    
    if is_processing:
        # 如果是處理中的消息，直接處理回應
        response = process_ai_response(agent, user_input, data.get('originalQuestion', ''))
    else:
        # 如果是新的用戶輸入，生成新的回應
        response = agent.think(user_input)
        
        # 檢查是否是 finish
        if_finish_match = re.search(r'<if_finish>(.*?)</if_finish>', response)
        if if_finish_match and if_finish_match.group(1).strip().lower() == 'finish':
            print("\n=== 檢測到 finish ===")
            content_match = re.search(r'<content>(.*?)</content>', response, re.DOTALL)
            if content_match:
                content = content_match.group(1).strip()
                print("\n=== AI 完整回應 ===")
                print(content)
                print("=== 回應結束 ===\n")
            else:
                print("未找到 content 標籤")
        else:
            print("\n=== 未檢測到 finish ===")
        
        # 處理回應
        processed_response = process_ai_response(agent, response, user_input)
        if processed_response != response:
            response = processed_response
    
    print(f"回應長度: {len(response)}")
    return jsonify({"response": response, "cycle_count": agent.cycle_count})

@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    data = request.json
    user_input = data.get('message', '')
    
    if not user_input:
        return jsonify({"error": "No message provided"}), 400
    
    def generate():
        # Get AI response
        response = agent.think(user_input)
        
        # Extract thinking steps
        thinking_steps = []
        strategy_matches = re.findall(r'<strategy>(.*?)</strategy>', response)
        think_matches = re.findall(r'<think>(.*?)</think>', response)
        
        # Combine strategy and think matches
        for i in range(max(len(strategy_matches), len(think_matches))):
            step = {}
            if i < len(strategy_matches):
                step['strategy'] = strategy_matches[i]
            if i < len(think_matches):
                step['think'] = think_matches[i]
            if step:
                thinking_steps.append(step)
                
                # Stream each thinking step
                yield f"data: {json.dumps({'type': 'thinking', 'data': step})}\n\n"
                time.sleep(0.5)  # Add delay for visual effect
        
        # Extract final content
        content_match = re.search(r'<content>(.*?)</content>', response, re.DOTALL)
        final_content = content_match.group(1) if content_match else response
        
        # Stream final response
        yield f"data: {json.dumps({'type': 'final', 'data': final_content})}\n\n"
        
        # Process AI response if needed (SQL queries, etc.)
        processed_response = process_ai_response(agent, response, user_input)
        if processed_response != response:
            # If there are additional steps, stream them
            yield f"data: {json.dumps({'type': 'processing', 'data': processed_response})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

def process_ai_response(agent, response, initial_input=None):
    """Process AI response similar to the main.py implementation"""
    print("\n=== 處理 AI 回應 ===")
    
    # 先檢查是否要結束
    if match := re.search(r'<if_finish>(.*?)</if_finish>', response):
        decision = match.group(1).strip().lower()
        print(f"檢測到 if_finish 標籤，決定: {decision}")
        
        if decision == 'finish':
            # 直接返回 finish 的回應，不做處理
            print("處理結果: 完成對話")
            return response
        elif decision == 'continue':
            print("處理結果: 繼續對話")
            # 只有在確定要繼續時才檢查動作
            if action_match := re.search(r'<action>(.*?)</action>', response):
                action = action_match.group(1)
                print(f"檢測到動作: {action[:50]}...")
                
                if action.startswith('READ_FILE '):
                    filename = action[10:]  # 去掉 'READ_FILE ' 前綴
                    print(f"讀取文件: {filename}")
                    file_content = agent.read_file(filename)
                    return agent.think(f"[SYSTEM] 我已經讀取了文件 {filename}，內容如下:\n{file_content}")
                
                elif action.startswith('SQL '):
                    sql = action[4:]  # 去掉 'SQL ' 前綴
                    print(f"執行 SQL: {sql[:50]}...")
                    result = agent.execute_sql(sql)
                    return agent.think(f"[SYSTEM] SQL 查詢結果如下:\n{result}")
                else:
                    print(f"未知動作: {action[:50]}...")
            else:
                print("未檢測到動作")
            
            # 如果沒有動作但要繼續，使用原始問題或通用提示
            next_input = f"[ORIGINAL_QUESTION] {initial_input}" if initial_input else "[SYSTEM] 請繼續分析上述情況。"
            print(f"使用下一個輸入: {next_input[:50]}...")
            return agent.think(next_input)
    else:
        print("未檢測到 if_finish 標籤")
    
    return response

@app.route('/api/reset', methods=['POST'])
def reset_conversation():
    print("\n=== 重置對話 ===")
    try:
        # 清空對話歷史文件
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
            print(f"已刪除歷史文件: {HISTORY_FILE}")
        
        # 重置 agent 的對話歷史和循環計數
        agent.conversation_history = []
        agent.cycle_count = 0
        print("已重置 agent 的對話歷史和循環計數")
        
        # 保存空的歷史
        agent.save_history()
        print("已保存空的歷史")
        
        return jsonify({"status": "success", "message": "對話已重置"})
    except Exception as e:
        print(f"重置對話時發生錯誤: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/')
def index():
    return send_from_directory('frontend', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('frontend', path)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
