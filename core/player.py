from typing import Dict, List, Any
import random

class PlayerAgent:
    def __init__(self, team: str):
        if team not in ["A", "B"]:
            raise ValueError("Team must be 'A' or 'B'")
        self.team = team
    
    def get_action(self, game_state: Dict[str, Any], available_pos: List[str]) -> Dict[str, Any]:
        raise NotImplementedError

class MockPlayerAgent(PlayerAgent):
    def __init__(self, team: str):
        super().__init__(team)
    
    def get_action(self, game_state: Dict[str, Any], available_pos: List[str]) -> Dict[str, Any]:
        if not available_pos:
            return {'reason': "No available moves.", 'action': {'way': None, 'pos': None}}
        
        return {
            'reason': "I am a mock agent, I choose randomly.",
            'action': {
                'way': random.choice(["left_to_right", "right_to_left"]),
                'pos': random.choice(available_pos),
            }
        }