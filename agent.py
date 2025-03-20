import os
import json
from openai import OpenAI
import pandas as pd
import sqlite3
from config import OPENAI_API_KEY, MODEL_NAME, HISTORY_FILE, FILES_DIR
from datetime import datetime
import re

class Agent:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.cycle_count = 0
        self.conversation_history = []
        # 不再自動載入歷史，而是在需要時載入
        self.setup_database()
        self.available_tables = self.get_available_tables()
        self.show_prompt = True  # 是否顯示 prompt

    def setup_database(self):
        """初始化 SQLite 數據庫並導入 CSV 文件"""
        self.db_path = os.path.join(FILES_DIR, 'data.db')
        # 不在初始化時創建連接，而是在需要時創建
        
        # 自動導入所有 CSV 文件到 SQLite
        conn = sqlite3.connect(self.db_path)
        for file in os.listdir(FILES_DIR):
            if file.endswith('.csv'):
                table_name = os.path.splitext(file)[0]
                df = pd.read_csv(os.path.join(FILES_DIR, file))
                df.to_sql(table_name, conn, if_exists='replace', index=False)
                print(f"已導入表格: {table_name}")
                # 顯示表格結構
                cursor = conn.cursor()
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                print("列名:", [col[1] for col in columns])
        conn.close()

    def get_available_tables(self):
        """獲取數據庫中所有可用的表及其結構"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        tables = {}
        
        # 獲取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        table_names = cursor.fetchall()
        
        # 獲取每個表的結構
        for (table_name,) in table_names:
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            tables[table_name] = [col[1] for col in columns]
        
        conn.close()
        return tables

    def execute_sql(self, sql):
        """執行 SQL 查詢並返回結果"""
        try:
            # 清理 SQL 語句，去除可能的大括號
            sql = sql.replace('{', '').replace('}', '')
            
            # 執行查詢
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(sql, conn)
            conn.close()
            
            # 限制回傳的資料量
            max_rows = 5  # 最多顯示 5 行
            max_column_length = 2000  # 每個欄位最多顯示 2000 字元
            max_total_length = 5000  # 總字數限制
            
            if len(df) > max_rows:
                df = df.head(max_rows)
            
            # 處理每個欄位的字數限制
            for column in df.columns:
                if df[column].dtype == 'object':  # 只處理文字欄位
                    df[column] = df[column].apply(lambda x: str(x)[:max_column_length] + '...' if len(str(x)) > max_column_length else x)
            
            # 轉換為字串
            result = df.to_string()
            
            # 處理總字數限制
            if len(result) > max_total_length:
                result = result[:max_total_length] + f"\n... (超過 {max_total_length} 字元限制)"
            
            # 如果有更多行未顯示，添加提示
            if len(df) > max_rows:
                result += f"\n... (還有 {len(df) - max_rows} 行未顯示)"
            
            return f"SQL 查詢結果 ({len(df)} 行):\n{result}"
            
        except Exception as e:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            table_names = cursor.fetchall()
            available_tables = "\n".join([f"- {table_name[0]}: " + ', '.join([col[1] for col in cursor.execute(f"PRAGMA table_info({table_name[0]})").fetchall()]) for table_name in table_names])
            conn.close()
            return f"SQL 執行錯誤: {str(e)}\n\n可用的表格和列：\n{available_tables}"

    def save_history(self):
        """保存對話歷史，包含完整的系統提示和對話內容"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = {
            "timestamp": current_time,
            "cycle_count": self.cycle_count,
            "system_prompt": self.last_system_prompt if hasattr(self, 'last_system_prompt') else None,
            "conversation": self.conversation_history[-1] if self.conversation_history else None,
            "full_context": self.last_full_context if hasattr(self, 'last_full_context') else None
        }
        
        # 如果是第一次寫入，創建新文件
        mode = 'w' if not os.path.exists(HISTORY_FILE) else 'a'
        with open(HISTORY_FILE, 'a', encoding='utf-8') as f:
            f.write("\n=== 新對話 ===\n")
            json.dump(entry, f, ensure_ascii=False, indent=2)
            f.write("\n")

    def load_history(self):
        """載入對話歷史"""
        self.conversation_history = []
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 分割每個對話記錄
                    conversations = content.split("=== 新對話 ===")
                    for conv in conversations:
                        if conv.strip():
                            try:
                                entry = json.loads(conv.strip())
                                if entry.get("conversation"):
                                    self.conversation_history.append(entry["conversation"])
                            except json.JSONDecodeError:
                                print(f"無法解析對話記錄: {conv[:100]}...")
            except Exception as e:
                print(f"載入對話歷史時發生錯誤: {e}")

    def format_history_for_ai(self):
        """格式化對話歷史，讓AI更容易理解"""
        formatted_history = []
        for entry in self.conversation_history:
            parts = entry.split("\n", 1)
            if len(parts) == 2 and parts[0].startswith("User: ") and "AI: " in parts[1]:
                user_msg = parts[0].replace("User: ", "")
                ai_msg = parts[1].replace("AI: ", "")
                formatted_history.append({
                    "user": user_msg,
                    "assistant": ai_msg
                })
        return formatted_history

    def read_file(self, filename):
        file_path = os.path.join(FILES_DIR, filename)
        if not os.path.exists(file_path):
            return f"Error: File {filename} not found"
        
        if filename.endswith('.csv'):
            df = pd.read_csv(file_path)
            return df.head().to_string()
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def think(self, user_input):
        self.cycle_count += 1
        
        print(f"\n=== Agent.think() 被調用，循環 #{self.cycle_count} ===")
        print(f"用戶輸入: {user_input[:100]}...")
        
        # 準備系統提示
        system_prompt = f"""你是一個可以閱讀本地文件和執行 SQL 查詢的法律案例分析專家。請你根據用戶的問題主動查詢相關案例分析回答
當前是第 {self.cycle_count} 次循環，你正在與自己對話進行法律分析

可用的資料表說明：
1. judgement_guilty_analysis_grouping_20250223_180510
   - 包含各爭點的有罪/無罪統計資料
   - 重要欄位：defendant_behavior (被告行為，用來搜尋關鍵字), issue_type (爭點), guilty (有罪/無罪) 可用來統計爭點下有無罪的案件比率
   - 可用於了解整體趨勢和常見爭點

2. judgement_raw_20250223_181106
   - 包含原始判決書內容
   - 使用 case_id 查詢特定案件的完整內容
   - 建議用法：SELECT * FROM judgement_raw_20250223_181106 WHERE case_id = '案件編號'

3. judgements_guilty_analysis_by_row_20250223_175846
   - 包含詳細的案件分析，每個爭點一行
   - 重要欄位：issue_type(爭點)、law_articles(法條)、guilty(有無罪)
   - 可用於深入分析特定爭點或法條的應用情況

分析建議：
1. 先用 grouping 表了解整體趨勢
2. 用 by_row 表深入分析特定爭點
3. 需要查看原始判決時，用 raw 表

可用的動作：
1. 讀取文件 (使用 READ_FILE 命令)
2. 執行 SQL 查詢 (使用 SQL 命令)
3. 決定是否繼續分析 (使用 if_finish 標籤)

SQL 查詢注意事項：
1. 不要在 SQL 語句外加大括號
2. 確保表名完全正確
3. 可嘗試檢視資料表內範例資料了解資料
4. 使用 LIKE 查詢時用 '%關鍵字%'
5. 每次查詢最多顯示 5 行資料
6. 單一欄位最多顯示 2000 字元
7. 查詢結果總字數限制為 5000 字元

請嚴格依照以下格式回應：
<think>思考方向 五十字內 </think>
<action>READ_FILE {{filename}} 或 SQL {{query}}</action>
<if_finish>continue 或 finish</if_finish>
<content>若完成則輸出針對用戶問題回答內容</content>
若你認為分析完成了請使用 finish,沒有則輸入 continue
若你決定 finish 請在 content 內總結到目前為止的發現與分析
回應的時候請盡量引用你搜尋到的數據、具體案例與事實，增加可信度
查到 3 個具體案例後請積極進行總結並 finish 對話
若用戶的問題跟法律無關請 finish 對話
"""

        # 保存最後的系統提示
        self.last_system_prompt = system_prompt
        
        # 準備消息
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # 添加所有歷史對話
        history = self.format_history_for_ai()
        for exchange in history:
            messages.append({"role": "user", "content": exchange["user"]})
            messages.append({"role": "assistant", "content": exchange["assistant"]})
        
        # 添加當前輸入
        messages.append({"role": "user", "content": user_input})
        
        # 保存完整上下文
        self.last_full_context = {
            "messages": messages,
            "show_prompt": self.show_prompt
        }
        
        # 顯示完整 prompt
        if self.show_prompt:
            print("\n=== 完整 Prompt ===")
            print("\n[SYSTEM]")
            print(system_prompt)
            print("\n[對話歷史]")
            for exchange in history:
                print("\n[USER]")
                print(exchange["user"])
                print("\n[ASSISTANT]")
                print(exchange["assistant"])
            print("\n[當前輸入]")
            print(user_input)
            print("\n=== Prompt 結束 ===\n")
        
        # 獲取 AI 回應
        print("正在獲取 AI 回應...")
        response = self.client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        print(f"AI 回應長度: {len(ai_response)}")
        
        # 檢查是否包含 finish 標籤
        if '<if_finish>finish</if_finish>' in ai_response:
            print("\n=== 檢測到 finish 標籤 ===")
            content_match = re.search(r'<content>(.*?)</content>', ai_response, re.DOTALL)
            if content_match:
                content = content_match.group(1).strip()
                print("\n=== AI 完整回應（agent.think 中檢測） ===")
                print(content)
                print("=== 回應結束 ===\n")
            else:
                print("未找到 content 標籤")
        
        self.conversation_history.append(f"User: {user_input}\nAI: {ai_response}")
        self.save_history()
        
        return ai_response
