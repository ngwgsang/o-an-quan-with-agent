# core/player.py
from typing import Dict, List, Any
import random
import os
from google import genai

from enum import Enum
from typing import List, Dict, Any, Optional, Type, TypeVar
from pydantic import BaseModel, Field
from .config import GEMINI_API_KEY, ALL_ENDPOINTS

from .memory import ShortTermMemory 

class DirectionOutput(str, Enum):
    CLOCKWISE = "clockwise"
    COUNTER_CLOCKWISE = "counter_clockwise"
    
class PositionOutput(str, Enum):
    A1 = "A1"
    A2 = "A2"
    A3 = "A3"
    A4 = "A4"
    A5 = "A5"
    B1 = "B1"
    B2 = "B2"
    B3 = "B3"
    B4 = "B4"
    B5 = "B5"
    
class ActionOutput(BaseModel):
     pos: PositionOutput = Field(description="Vị trí được chọn làm ô bắt đầu")
     way: DirectionOutput = Field(description="Chiều đi được lựa chọn")
    
class PlayerAgentOutput(BaseModel):
    reason: Optional[str] = Field(description="Suy nghĩ của Agent về lý do để chọn nước đi này")
    action: ActionOutput = Field(description="Hành động được lựa chọn bởi Agent")

class PersonaInstruction(str, Enum):
    ATTACK = "Aggressive Attacker"
    DEFENSE = "Cautious Defender"
    BALANCE = "Balanced Player"
    STRATEGIC = "Strategic Planner"
    def get_prompt(self) -> str:
        if self == PersonaInstruction.ATTACK:
            return "I am an aggressive player who is willing to take risks to win. My goal is to capture as many pieces as possible, especially the Mandarin. I will look for moves that can create long capture chains, even if it might leave my own cells empty."
        elif self == PersonaInstruction.DEFENSE:
            return "I am a defensive player who prioritizes protecting my territory. I will try to keep my cells from being empty and avoid risky moves that could allow the opponent to counter-attack. My goal is to maintain a stable position and wait for an opportunity."
        elif self == PersonaInstruction.BALANCE:
            return "I am a balanced player, combining offense and defense. I will consider both gaining pieces and maintaining a safe board position before making a decision. I am not overly risky but also don't miss good opportunities to capture pieces."
        elif self == PersonaInstruction.STRATEGIC:
            return "I am a strategic player who thinks long-term. I will calculate moves to create favorable situations in the future, such as concentrating pieces in strategic positions or forcing the opponent into a difficult spot. I prioritize board control over immediate captures."
        return ""

class PlayerAgent:
    def __init__(self, team: str, persona: PersonaInstruction, model: str = "gemini-2.0-flash-lite", temperature: float = 0.7, top_p: float = 1.0, top_k: int = 40, mem_size: Optional[int] = None):
        if team not in ["A", "B"]:
            raise ValueError("Team must be 'A' or 'B'")
        self.team = team
        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.keys = GEMINI_API_KEY
        # self.thoughts = ["GAME START. Nothing in memory!!!"]

        checked_mem_size = mem_size if mem_size is not None else 5
        self.memory = ShortTermMemory(int(checked_mem_size)) # Lưu xxx lượt gần nhất

        self.persona = persona
        self._rules_template = self.get_rule()

    def get_rule(self) -> str:
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            rules_path = os.path.join(current_dir, 'game_rules.md')
            with open(rules_path, 'r', encoding='utf-8') as f:
                return f.read()
            
        except FileNotFoundError:
            print(f"Lỗi: Không tìm thấy file game_rules.md tại đường dẫn mong muốn.")
            return "Lỗi: Không thể tải luật chơi."
    
    def get_key(self):
        return random.choice(self.keys)
    
    def get_prompt(self, game_state, available_pos):
        
        round_idx = game_state["round"]
        board = game_state["board"]
        persona_instruction = self.persona.get_prompt()

        memory_list = self.memory.get_context()
        memory_context = "\n".join(memory_list)

        game_rules = self._rules_template

        prompt = f"""
        ---
        **BỐI CẢNH (GAME CONTEXT)**

        Bạn là một người chơi thông minh trong trò chơi Ô Ăn Quan của Việt Nam.
        Đây là trạng thái bàn cờ hiện tại sau khi đối thủ đã đi:
        {board}

        [LƯỢT {round_idx}/30]
        {f"Cảnh báo: Trò chơi sẽ kết thúc sau {30 - round_idx}" if round_idx > 20 else "" } lượt nữa.

        Bạn là Người chơi {self.team}.
        Thứ tự các ô trên bàn cờ: QA → A1 → A2 → A3 → A4 → A5 → QB → B1 → B2 → B3 → B4 → B5
        Các ô bạn có thể bắt đầu đi: {available_pos}

        **KÝ ỨC GẦN ĐÂY (MEMORY)**
        (Từ mới nhất đến cũ nhất)
        {memory_context}

        ---
        **LUẬT CHƠI (GAME RULES)**
        {game_rules}

        ---
        **TÍNH CÁCH (PERSONA)**
        {persona_instruction}

        ---
        **NHIỆM VỤ (TASK)**
        Dựa vào luật chơi và tình hình bàn cờ, hãy suy nghĩ và lựa chọn nước đi tốt nhất. Phân tích các yếu tố sau:
        1.  Nên chọn ô nào (`pos`) để bắt đầu?
        2.  Nên đi theo hướng nào (`way`)?
        3.  Nước đi này có phù hợp với tính cách và chiến thuật của bạn không?
        4.  Hãy giải thích ngắn gọn lý do (`reason`) cho lựa chọn của bạn.

        ---"""
        return prompt 
    
    def get_action(self, game_state: Dict[str, Any], available_pos: List[str]) -> Dict[str, Any]:
        client = genai.Client(api_key=self.get_key())
        prompt = self.get_prompt(game_state, available_pos)

        response = client.models.generate_content(
            model=self.model,
            contents=self.get_prompt(game_state, available_pos),
            config={
                "response_mime_type": "application/json",
                "response_schema": PlayerAgentOutput,
                "temperature": self.temperature,
                "top_p": self.top_p,
                "top_k": self.top_k,
            },
        ).parsed.model_dump()

        print("MODEL IN USE: ", self.model)
        
        # self.thoughts.append(response["reason"])
        self.memory.add_memory(
            round_num=game_state["round"],
            thought=response["reason"],
            action=response["action"]
        )

        response['memory_context'] = self.memory.get_context()
        
        # Add thoughts to the response
        # response['thoughts'] = self.thoughts

        # print("Player thoughts:", response)
        print("Player thoughts:", response['reason'])
        response['thoughts'] = response['reason']
        return response

class MockPlayerAgent(PlayerAgent):
    def __init__(self, team: str, persona: PersonaInstruction, **kwargs):
        super().__init__(team, persona, **kwargs)
    
    def get_action(self, game_state: Dict[str, Any], available_pos: List[str]) -> Dict[str, Any]:
        if not available_pos:
            return {'reason': "No available moves.", 'action': {'way': None, 'pos': None}, 'memory_context': self.memory.get_context()}
        
        # self.thoughts.append("I am a mock agent, I choose randomly.")
        reason = "I am a mock agent, I choose randomly."

        action = {
            'way': random.choice(["clockwise", "counter_clockwise"]),
            'pos': random.choice(available_pos),
        }
        
        self.memory.add_memory(
            round_num=game_state["round"],
            thought=reason,
            action=action
        )

        return {
            'reason': reason,
            'action': action,
            'memory_context': self.memory.get_context()
        }
