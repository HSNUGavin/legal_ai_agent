import re
import os
from agent import Agent

def process_ai_response(agent, response, initial_input=None):
    """處理 AI 的回應，包括執行動作和處理結果"""
    # 先檢查是否要結束
    if match := re.search(r'<if_finish>(.*?)</if_finish>', response):
        decision = match.group(1).strip().lower()
        if decision == 'finish':
            return response
        elif decision == 'continue':
            # 只有在確定要繼續時才檢查動作
            if action_match := re.search(r'<action>(.*?)</action>', response):
                action = action_match.group(1)
                if action.startswith('READ_FILE '):
                    filename = action[10:]  # 去掉 'READ_FILE ' 前綴
                    print(f"\n讀取文件 {filename}:")
                    file_content = agent.read_file(filename)
                    print(file_content)
                    
                    print(f"\n循環次數: {agent.cycle_count + 1}")
                    print("AI處理文件內容...")
                    return agent.think(f"[SYSTEM] 我已經讀取了文件 {filename}，內容如下:\n{file_content}")
                
                elif action.startswith('SQL '):
                    sql = action[4:]  # 去掉 'SQL ' 前綴
                    print(f"\n執行 SQL: {sql}")
                    result = agent.execute_sql(sql)
                    print(result)
                    
                    print(f"\n循環次數: {agent.cycle_count + 1}")
                    print("AI處理 SQL 結果...")
                    return agent.think(f"[SYSTEM] SQL 查詢結果如下:\n{result}")
            
            # 如果沒有動作但要繼續，使用原始問題或通用提示
            print(f"\n循環次數: {agent.cycle_count + 1}")
            print("AI 繼續分析...")
            next_input = f"[ORIGINAL_QUESTION] {initial_input}" if initial_input else "[SYSTEM] 請繼續分析上述情況。"
            return agent.think(next_input)
    
    return response

def main():
    # 檢查是否需要重置記憶
    if os.path.exists("conversation_history.txt"):
        reset = input("是否要重置對話記憶？(y/n): ").lower() == 'y'
        if reset:
            os.remove("conversation_history.txt")
            print("對話記憶已重置")
    
    agent = Agent()
    print("系統啟動 (輸入 'exit' 結束)")
    print("CSV 文件已自動導入到 SQLite 數據庫中")
    
    while True:
        user_input = input("\n請輸入: ")
        if user_input.lower() == 'exit':
            break
            
        print(f"\n循環次數: {agent.cycle_count + 1}")
        print("AI思考中...")
        
        # 獲取並處理 AI 的回應
        response = agent.think(user_input)
        while True:
            print("\n" + response)
            processed_response = process_ai_response(agent, response, user_input)
            if processed_response == response:  # 如果回應沒有改變，說明不需要繼續處理
                break
            response = processed_response

if __name__ == "__main__":
    main()
