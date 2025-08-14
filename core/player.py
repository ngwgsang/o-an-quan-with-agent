# core/player.py
from typing import Dict, List, Any
import random
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
    def __init__(self, team: str, persona: PersonaInstruction, model: str = "gemini-2.0-flash-lite", temperature: float = 0.7, top_p: float = 1.0, top_k: int = 40):
        if team not in ["A", "B"]:
            raise ValueError("Team must be 'A' or 'B'")
        self.team = team
        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.keys = GEMINI_API_KEY
        # self.thoughts = ["GAME START. Nothing in memory!!!"]
        self.memory = ShortTermMemory(window_size=5) # Lưu 5 lượt gần nhất
        self.persona = persona
    
    def get_key(self):
        return random.choice(self.keys)
    
    def get_prompt(self, game_state, available_pos):
        
        round_idx = game_state["round"]
        board = game_state["board"]
        persona_instruction = self.persona.get_prompt()

        memory_context = self.memory.get_context()

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

        **My Recent Memories (from most recent to oldest)**
        {memory_context}

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
        **Persona**
        {persona_instruction}

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
