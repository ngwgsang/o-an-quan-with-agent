# core/player.py
from typing import Dict, List, Any
import random
from google import genai

from enum import Enum
from typing import List, Dict, Any, Optional, Type, TypeVar
from pydantic import BaseModel, Field
from .config import GEMINI_API_KEY, ALL_ENDPOINTS

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
    def __init__(self, team: str, model: str = "gemini-2.0-flash-lite", temperature: float = 0.7, top_p: float = 1.0, top_k: int = 40):
        if team not in ["A", "B"]:
            raise ValueError("Team must be 'A' or 'B'")
        self.team = team
        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.keys = GEMINI_API_KEY
        self.thoughts = ["GAME START. Nothing in memory!!!"]
    
    def get_key(self):
        return random.choice(self.keys)
    
    def get_prompt(self, game_state, available_pos):
        
        round_idx = game_state["round"]
        board = game_state["board"]
        
        prompt = f"""
        ---
        **Game States**

        You are an intelligent agent playing the traditional Vietnamese game "Ô Ăn Quan".
        
        After the opponent takes action, here is the current board state:
        {board}

        [ROUND {round_idx}/30]
        {f"Warning: The game will end after {30 - round_idx}" if round_idx > 20 else "" } round.

        You are Player {self.team}.
        Position Order: QA → A1 → A2 → A3 → A4 → A5 → QB → B1 → B2 → B3 → B4 → B5
        Your available positions to choose from: {available_pos}

        My thoughts on the previous round:
        {self.thoughts[-1]}

        ---
        **Game Rules**

        1. You can only move from one of your 5 owned positions (e.g., A1 - A5 for Player A).
        2. A move consists of picking up all peasants (not mandarin) from a cell and scattering them one-by-one in a direction.
        3. There are 2 directions: **clockwise** and **counterclockwise** (relative to the board layout).
        4. After scattering, if the next cell is empty, and the one after it has peasants or mandarin (with enough tokens), you can **capture** the tokens there.
        5. If that captured cell is not a Mandarin or a Mandarin with less than 5 tokens (Immature Mandarin), capturing is **not allowed**.
        6. After a capture, if the next cell contains tokens, you **continue scattering**.
        7. Mandarin tokens are **never moved**, only captured. Each token captured adds to your score Mandarin (5pt) and Peasant (1pt). 
        8. If your side is empty and you have ≥ 5 points, you must "pay" 7 points to restore 5 peasant (1 peasant per cell).
        9. The game ends when **both Mandarin are captured** or players can no longer move.
        10. Can't capture Mandarin at early game round 1 - 2.

        ---
        **Task**
        Based on the above rules and current game state, think about:

        - Which position should you pick to scatter from?
        - Which direction to scatter?
        - Which move fits your strategy?

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
        
        self.thoughts.append(response["reason"])
        
        # Add thoughts to the response
        response['thoughts'] = self.thoughts
        print("Player thoughts:", response)
        return response

class MockPlayerAgent(PlayerAgent):
    def __init__(self, team: str, **kwargs):
        super().__init__(team, **kwargs)
    
    def get_action(self, game_state: Dict[str, Any], available_pos: List[str]) -> Dict[str, Any]:
        if not available_pos:
            return {'reason': "No available moves.", 'action': {'way': None, 'pos': None}, 'thoughts': self.thoughts}
        
        self.thoughts.append("I am a mock agent, I choose randomly.")
        return {
            'reason': "I am a mock agent, I choose randomly.",
            'action': {
                'way': random.choice(["clockwise", "counter_clockwise"]),
                'pos': random.choice(available_pos),
            },
            'thoughts': self.thoughts
        }