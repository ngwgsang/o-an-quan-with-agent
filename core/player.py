# core/player.py
import os
import random

from google import genai
from typing import Dict, List, Any
from enum import Enum
from typing import List, Dict, Any, Optional, Type, TypeVar
from pydantic import BaseModel, Field
from .config import GEMINI_API_KEY
from .memory import ShortTermMemory 
from .rule import get_rules_as_str
from .persona_intruct import ATTACKER, DEFENDER, BALANCED, STRATEGIC, BasePersona


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

class PlayerAgent:
    def __init__(self, team: str, persona: BasePersona, model: str = "gemini-2.0-flash-lite", temperature: float = 0.7, top_p: float = 1.0, top_k: int = 40, mem_size: Optional[int] = None):
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

        self.persona: BasePersona = persona
    
    def get_key(self):
        return random.choice(self.keys)

    def get_prompt(self, game_state, available_pos, extended_rule) -> str:
        
        round_idx = game_state["round"]
        board = game_state["board"]
        persona_text = f"""
        Characteristics: {", ".join(self.persona.characteristics)}
        Typical strategy: {", ".join(self.persona.typical_strategy)}
        Example: {self.persona.case_example}
        """

        memory_list = self.memory.get_context()
        memory_context = "\n".join(memory_list)

        game_rules = get_rules_as_str(extended_rules=extended_rule)

        prompt = f"""
        ---
        **GAME CONTEXT**

        You are an intelligent player in the Vietnamese game "O An Quan".
        This is the current board state after the opponent's move:
        {board}

        [ROUND {round_idx}/30]
        {f"Warning: The game will end in {30 - round_idx} more rounds." if round_idx > 20 else "" }

        You are Player {self.team}.
        The order of squares on the board (clockwise): QA → A1 → A2 → A3 → A4 → A5 → QB → B1 → B2 → B3 → B4 → B5
        Your available starting positions: {available_pos}

        **RECENT MEMORY**
        (From newest to oldest)
        {memory_context}

        ---
        **GAME RULES**
        {game_rules}

        ---
        **PERSONA**
        {persona_text}

        ---
        **TASK**
        Based on the game rules and the current board state, think and choose the best move. Analyze the following factors:
        1.  Which square (`pos`) should you start from?
        2.  Which direction (`way`) should you go?
        3.  Does this move align with your persona and strategy?
        4.  Briefly explain the reasoning (`reason`) for your choice.

        ---"""
        print(prompt)
        return prompt 
    
    def get_action(self, game_state: Dict[str, Any], available_pos: List[str], extended_rule=None) -> Dict[str, Any]:
        client = genai.Client(api_key=self.get_key())
        
        response = client.models.generate_content(
            model=self.model,
            contents=self.get_prompt(game_state, available_pos, extended_rule),
            config={
                "response_mime_type": "application/json",
                "response_schema": PlayerAgentOutput,
                "temperature": self.temperature,
                "top_p": self.top_p,
                "top_k": self.top_k,
            },
        ).parsed.model_dump()

        print("MODEL IN USE: ", self.model)
        
        self.memory.add_memory(
            round_num=game_state["round"],
            thought=response["reason"],
            action=response["action"]
        )

        response['memory_context'] = self.memory.get_context()
        print("Player thoughts:", response['reason'])
        response['thoughts'] = response['reason']
        return response

class MockPlayerAgent(PlayerAgent):
    def __init__(self, team: str, persona: BasePersona, **kwargs):
        super().__init__(team, persona, **kwargs)
    
    def get_action(self, game_state: Dict[str, Any], available_pos: List[str]) -> Dict[str, Any]:
        if not available_pos:
            return {'reason': "No available moves.", 'action': {'way': None, 'pos': None}, 'memory_context': self.memory.get_context()}
        
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
