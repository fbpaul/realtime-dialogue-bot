import uuid
import os
import sys
from typing import Dict, Optional
import asyncio
from app.config import config

# 加入 llm_tools 路徑
sys.path.append('/app/llm_tools')

class ChatService:
    def __init__(self):
        # 儲存對話歷史（簡單版本，生產環境建議用資料庫）
        self.conversations: Dict[str, list] = {}
        self.llm_chat = None
        self.use_llm_tools = True  # 預設使用 llm_tools
        
        # 從配置文件載入參數
        self._load_config()
    
    def _load_config(self):
        """從配置文件載入聊天服務參數"""
        chat_config = config.get_chat_config()
        self.use_llm_tools = chat_config.get("use_llm_tools", self.use_llm_tools)
        self.device = chat_config.get("device", "auto")
        self.llm_tools_device = chat_config.get("llm_tools_device", self.device)
        print(f"Chat 配置載入: use_llm_tools={self.use_llm_tools}, device={self.device}, llm_tools_device={self.llm_tools_device}")
        
    async def initialize_llm(self, use_llm_tools: bool = None, 
                           llm_tools_config: str = None, 
                           llm_tools_model: str = None,
                           local_model_path: str = None):
        """初始化 LLM 聊天服務
        
        Args:
            use_llm_tools: 是否使用 llm_tools 配置
            llm_tools_config: llm_tools 配置檔案路徑
            llm_tools_model: llm_tools 中的模型名稱
            local_model_path: 本地模型路徑（如果不使用 llm_tools）
        """
        # 使用傳入參數或配置文件中的值
        if use_llm_tools is not None:
            self.use_llm_tools = use_llm_tools
        
        try:
            if self.use_llm_tools:
                # 使用 llm_tools 配置
                from llm_chat import LLMChat
                
                # 從配置文件獲取參數
                chat_config = config.get_chat_config()
                config_path = llm_tools_config or chat_config.get("llm_tools_config", "/app/llm_tools/configs/models.yaml")
                model_name = llm_tools_model or chat_config.get("llm_tools_model", "Qwen2.5-32B-Instruct-GPTQ-Int4")
                
                if not os.path.exists(config_path):
                    print(f"LLM 配置檔案不存在: {config_path}")
                    raise FileNotFoundError(f"配置檔案不存在: {config_path}")
                    
                self.llm_chat = LLMChat(
                    model=model_name, 
                    config_path=config_path,
                )
                print(f"LLM 聊天服務初始化完成! (使用 llm_tools, 模型: {model_name}, 設備: {self.llm_tools_device})")
            
            else:
                # 使用本地模型（可以在這裡實作本地模型載入）
                print("本地模型模式尚未實作，改用 llm_tools")
                await self.initialize_llm(use_llm_tools=True, 
                                        llm_tools_config=llm_tools_config,
                                        llm_tools_model=llm_tools_model)
                
        except Exception as e:
            print(f"LLM 初始化失敗: {e}")
            print("將使用簡單聊天模式")
            self.llm_chat = None
    
    async def get_response(self, user_message: str, conversation_id: Optional[str] = None) -> Dict:
        """取得機器人回覆"""
        try:
            # 如果沒有對話 ID，建立新的
            if not conversation_id:
                conversation_id = str(uuid.uuid4())
            
            # 確保對話歷史存在
            if conversation_id not in self.conversations:
                self.conversations[conversation_id] = []
            
            # 產生機器人回覆
            if self.llm_chat:
                # 使用 LLM 產生回覆
                bot_response = await self._generate_llm_response(user_message, conversation_id)
            else:
                # 使用簡單回覆邏輯
                bot_response = await self._generate_simple_response(user_message, self.conversations[conversation_id])
            
            # 更新對話歷史
            self.conversations[conversation_id].append({
                "role": "user",
                "content": user_message
            })
            self.conversations[conversation_id].append({
                "role": "assistant", 
                "content": bot_response
            })
            
            # 限制對話歷史長度（避免記憶體過度使用）
            if len(self.conversations[conversation_id]) > 20:
                self.conversations[conversation_id] = self.conversations[conversation_id][-20:]
            
            return {
                "message": bot_response,
                "conversation_id": conversation_id
            }
        
        except Exception as e:
            print(f"聊天處理錯誤: {e}")
            raise Exception(f"無法產生回覆: {str(e)}")
    
    async def _generate_llm_response(self, user_message: str, conversation_id: str) -> str:
        """使用 LLM 產生回覆"""
        try:
            # 取得對話歷史
            history = self.conversations.get(conversation_id, [])
            
            # 轉換成 LLM 所需的格式
            llm_history = []
            for msg in history:
                llm_history.append({
                    'role': msg['role'],
                    'content': msg['content']
                })
            
            # 呼叫 LLM
            response, _ = self.llm_chat.chat(
                query=user_message,
                history=llm_history,
                system="你是一個親切友善的語音助理，會用繁體中文回答問題。請保持回覆簡潔有趣，適合語音對話。"
            )
            
            return response.strip()
            
        except Exception as e:
            print(f"LLM 回覆產生錯誤: {e}")
            # 如果 LLM 失敗，回到簡單模式
            return await self._generate_simple_response(user_message, self.conversations.get(conversation_id, []))
    
    async def _generate_simple_response(self, user_message: str, conversation_history: list) -> str:
        """產生機器人回覆（簡單版本，可以後續擴展）"""
        
        # 簡單的回覆邏輯（可以後續替換成 LLM API）
        user_message_lower = user_message.lower().strip()
        
        # 問候語
        if any(greeting in user_message_lower for greeting in ["你好", "哈囉", "嗨", "hello", "hi"]):
            responses = [
                "你好！很高興跟你聊天！有什麼我可以幫助你的嗎？",
                "嗨！我是你的語音助理，有什麼想聊的嗎？",
                "哈囉！今天過得如何？"
            ]
            import random
            return random.choice(responses)
        
        # 天氣相關
        elif any(weather in user_message_lower for weather in ["天氣", "氣溫", "下雨", "晴天"]):
            return "我無法查詢即時天氣，但建議你可以查看氣象局或天氣 App 獲得最準確的資訊喔！"
        
        # 時間相關
        elif any(time_word in user_message_lower for time_word in ["時間", "幾點", "現在"]):
            from datetime import datetime
            now = datetime.now()
            return f"現在是 {now.strftime('%Y年%m月%d日 %H點%M分')}。"
        
        # 自我介紹
        elif any(intro in user_message_lower for intro in ["你是誰", "自我介紹", "你叫什麼"]):
            return "我是一個語音對話機器人，可以跟你聊天、回答問題。我支援語音輸入和語音回覆，讓對話更自然！"
        
        # 功能詢問
        elif any(func in user_message_lower for func in ["功能", "能做什麼", "會什麼"]):
            return "我可以：\n1. 聽懂你的語音並轉成文字\n2. 跟你聊天對話\n3. 把回覆用語音唸出來\n4. 記住我們的對話內容\n還有什麼想知道的嗎？"
        
        # 道別
        elif any(bye in user_message_lower for bye in ["再見", "掰掰", "拜拜", "bye", "goodbye"]):
            return "再見！很高興跟你聊天，期待下次見面！"
        
        # 謝謝
        elif any(thanks in user_message_lower for thanks in ["謝謝", "感謝", "thanks", "thank you"]):
            return "不客氣！很高興能幫到你！還有其他需要協助的嗎？"
        
        # 預設回覆
        else:
            responses = [
                f"你說「{user_message}」，這很有趣！可以告訴我更多嗎？",
                f"關於「{user_message}」這個話題，我想了解你的想法。",
                "這個問題很棒！雖然我還在學習中，但我很願意跟你討論。",
                "有趣的觀點！你可以再詳細說明一下嗎？",
                "我正在思考你的話。可以換個方式問問看嗎？"
            ]
            import random
            return random.choice(responses)
    
    def get_conversation_history(self, conversation_id: str) -> Optional[list]:
        """取得對話歷史"""
        return self.conversations.get(conversation_id)
    
    def clear_conversation(self, conversation_id: str) -> bool:
        """清除對話歷史"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            return True
        return False
    
    def get_active_conversations(self) -> list:
        """取得所有活躍對話的 ID"""
        return list(self.conversations.keys())
