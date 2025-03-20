import os
import json
from openai import OpenAI
import pandas as pd
import sqlite3
from config import OPENAI_API_KEY, MODEL_NAME, HISTORY_DIR, HISTORY_FILE, FILES_DIR
from datetime import datetime
import uuid

class Agent:
    def __init__(self, conversation_id=None):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.cycle_count = 0
        self.conversation_history = []
        self.conversation_id = conversation_id or str(uuid.uuid4())
        self.load_history()
        self.setup_database()
        self.available_tables = self.get_available_tables()
        self.show_prompt = True

    def get_history_file(self):
        """獲取特定對話的歷史文件路徑"""
        return os.path.join(HISTORY_DIR, f"conversation_{self.conversation_id}.json")

    def load_history(self):
        """加載特定對話的歷史記錄"""
        history_file = self.get_history_file()
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history_data = []
                    for line in f:
                        if line.strip():  # 忽略空行
                            try:
                                entry = json.loads(line)
                                if entry.get("conversation"):
                                    history_data.append(entry["conversation"])
                            except json.JSONDecodeError:
                                continue
                    if history_data:
                        self.conversation_history = history_data[-1] if history_data else []
                        self.cycle_count = history_data[-1].get("cycle_count", 0) if history_data else 0
            except Exception as e:
                print(f"加載歷史記錄時出錯: {e}")
        else:
            self.conversation_history = []
            self.cycle_count = 0

    def save_history(self):
        """保存對話歷史，包含完整的系統提示和對話內容"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = {
            "timestamp": current_time,
            "conversation_id": self.conversation_id,
            "cycle_count": self.cycle_count,
            "system_prompt": self.last_system_prompt if hasattr(self, 'last_system_prompt') else None,
            "conversation": self.conversation_history[-1] if self.conversation_history else None,
            "full_context": self.last_full_context if hasattr(self, 'last_full_context') else None
        }
        
        # 保存到特定對話的文件
        history_file = self.get_history_file()
        with open(history_file, 'a', encoding='utf-8') as f:
            json.dump(entry, f, ensure_ascii=False)
            f.write("\n")
        
        # 同時保存到主歷史文件
        with open(HISTORY_FILE, 'a', encoding='utf-8') as f:
            json.dump(entry, f, ensure_ascii=False)
            f.write("\n")

    @staticmethod
    def list_conversations():
        """列出所有可用的對話"""
        history_dir = HISTORY_DIR
        conversations = []
        if os.path.exists(history_dir):
            for file in os.listdir(history_dir):
                if file.startswith("conversation_") and file.endswith(".json"):
                    conv_id = file[12:-5]  # 移除 "conversation_" 和 ".json"
                    try:
                        with open(os.path.join(history_dir, file), 'r', encoding='utf-8') as f:
                            for line in f:
                                if line.strip():
                                    try:
                                        entry = json.loads(line)
                                        conversations.append({
                                            "id": conv_id,
                                            "last_update": entry["timestamp"],
                                            "messages_count": len(entry.get("conversation", [])) if entry.get("conversation") else 0
                                        })
                                        break
                                    except json.JSONDecodeError:
                                        continue
                    except Exception as e:
                        print(f"讀取對話 {conv_id} 時出錯: {e}")
        return conversations

    def setup_database(self):
        """初始化 SQLite 數據庫並導入 CSV 文件"""
        self.db_path = os.path.join(FILES_DIR, 'data.db')
        self.conn = sqlite3.connect(self.db_path)
        
        # 自動導入所有 CSV 文件到 SQLite
        for file in os.listdir(FILES_DIR):
            if file.endswith('.csv'):
                table_name = os.path.splitext(file)[0]
                df = pd.read_csv(os.path.join(FILES_DIR, file))
                df.to_sql(table_name, self.conn, if_exists='replace', index=False)
                print(f"已導入表格: {table_name}")
                # 顯示表格結構
                cursor = self.conn.cursor()
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                print("列名:", [col[1] for col in columns])

    def get_available_tables(self):
        """獲取數據庫中所有可用的表及其結構"""
        cursor = self.conn.cursor()
        tables = {}
        
        # 獲取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        table_names = cursor.fetchall()
        
        # 獲取每個表的結構
        for (table_name,) in table_names:
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            tables[table_name] = [col[1] for col in columns]
        
        return tables

    def execute_sql(self, sql):
        """執行 SQL 查詢並返回結果"""
        try:
            # 清理 SQL 語句，去除可能的大括號
            sql = sql.replace('{', '').replace('}', '')
            
            # 執行查詢
            df = pd.read_sql_query(sql, self.conn)
            
            # 限制回傳的資料量
            max_rows = 5  # 最多顯示 5 行
            max_str_length = 500  # 每個欄位最多顯示 500 字元
            max_total_length = 5000  # 整體輸出最大長度
            
            if len(df) > max_rows:
                df = df.head(max_rows)
            
            # 截斷長字串
            for col in df.columns:
                if df[col].dtype == 'object':  # 只處理字串類型
                    df[col] = df[col].apply(lambda x: str(x)[:max_str_length] + '...' if len(str(x)) > max_str_length else x)
            
            # 轉換為字串並限制總長度
            result = df.to_string()
            if len(result) > max_total_length:
                result = result[:max_total_length] + "..."
            
            return f"SQL 查詢結果 ({len(df)} 行):\n{result}"
            
        except Exception as e:
            # 簡化錯誤訊息
            error_msg = str(e)
            if len(error_msg) > 100:
                error_msg = error_msg[:100] + "..."
            
            # 只顯示前三個表格的資訊
            available_tables_list = [f"- {table}: {columns}" for table, columns in list(self.available_tables.items())[:3]]
            if len(self.available_tables) > 3:
                available_tables_list.append("...")
            available_tables = "\n".join(available_tables_list)
            
            return f"SQL 執行錯誤: {error_msg}\n\n可用的表格和列（部分）：\n{available_tables}"

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
        """讀取文件內容，並限制輸出長度"""
        file_path = os.path.join(FILES_DIR, filename)
        if not os.path.exists(file_path):
            return f"Error: File {filename} not found"
        
        max_total_length = 1000  # 最大輸出長度
        
        if filename.endswith('.csv'):
            df = pd.read_csv(file_path)
            # 只顯示前 5 行和前 5 列
            preview_df = df.head().iloc[:, :5]
            if df.shape[1] > 5:
                preview_df = preview_df.assign(**{'...': ['...'] * len(preview_df)})
            result = preview_df.to_string()
            if len(result) > max_total_length:
                result = result[:max_total_length] + "..."
            return f"文件預覽 (顯示前 5 行):\n{result}"
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(max_total_length)
                if len(content) == max_total_length:
                    content += "..."
                return content
        except UnicodeDecodeError:
            return "Error: 無法讀取二進制文件"

    def think(self, user_input):
        self.cycle_count += 1
        
        # 如果是第一次對話，保存初始問題
        if self.cycle_count == 1:
            self.initial_question = user_input
        
        # 準備系統提示
        system_prompt = f"""你是一個可以閱讀本地文件和執行 SQL 查詢的法律案例分析專家。請你根據用戶的問題主動查詢相關案例分析回答
當前是第 {self.cycle_count} 次循環，你正在與自己對話進行法律分析

用戶的初始問題是：{self.initial_question if hasattr(self, 'initial_question') else user_input} 請根據這個問題進行回答

可用的資料表說明：
1. judgement_guilty_analysis_grouping_20250223_180510
   - 包含各爭點的有罪/無罪統計資料
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
3. 決定是否繼續分析 (使用 if_finish 標籤)，當你充分分析後，請使用 finish

SQL 查詢注意事項：
1. 不要在 SQL 語句外加大括號
2. 確保表名完全正確
3. 可嘗試檢視資料表內範例資料了解資料
4. 使用 LIKE 查詢時用 '%關鍵字%'
5. 每次查詢最多顯示 5 行資料
6. 長文字欄位會自動截斷

請嚴格依照以下格式回應：
<think summary>十字內 思考方向</think summary>
<think>三十字內 思考過程，包括對之前對話的理解和下一步計劃</think>
<action>READ_FILE {{filename}} 或 SQL {{query}}</action>
<content>回應內容，包括分析的結果</content>
<if_finish>continue 或 finish</if_finish>
若你認為分析完成了請使用 finish,沒有則輸入 continue
若你決定 finish 請在 content 內總結到目前為止的發現與分析
回應的時候請盡量引用你搜尋到的數據、具體案例與事實，增加可信度
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
        response = self.client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        self.conversation_history.append(f"User: {user_input}\nAI: {ai_response}")
        self.save_history()
        
        return ai_response
