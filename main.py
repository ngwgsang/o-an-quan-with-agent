from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
import random
import uvicorn

# =============================================================================
# LOGIC GAME Ô ĂN QUAN
# =============================================================================

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
            return {'think': "No available moves.", 'way': None, 'pos': None}
        return {
            'think': "I am a mock agent, I choose randomly.",
            'way': random.choice(["left_to_right", "right_to_left"]),
            'pos': random.choice(available_pos),
        }

class Enviroment:
    def __init__(self):
        self.players_map = {"A": [f"A{i}" for i in range(1, 6)], "B": [f"B{i}" for i in range(1, 6)]}
        self.reset()

    def reset(self):
        self.game_state = {
            "board": {
                "QA": ["mandarin_a"], "A1": ["peasant_a"] * 5, "A2": ["peasant_a"] * 5,
                "A3": ["peasant_a"] * 5, "A4": ["peasant_a"] * 5, "A5": ["peasant_a"] * 5,
                "QB": ["mandarin_b"], "B1": ["peasant_b"] * 5, "B2": ["peasant_b"] * 5,
                "B3": ["peasant_b"] * 5, "B4": ["peasant_b"] * 5, "B5": ["peasant_b"] * 5,
            },
            "score": {"A": 0, "B": 0},
            "round": 0
        }

    def get_game_state(self) -> Dict[str, Any]:
        return self.game_state

    def get_available_pos(self, player_team: str) -> List[str]:
        board = self.game_state["board"]
        return [pos for pos in self.players_map[player_team] if board.get(pos) and not pos.startswith("Q")]

    def restore_peasants(self, player_team: str) -> tuple[bool, str]:
        score = self.game_state["score"]
        board = self.game_state["board"]
        message = ""
        can_continue = True
        
        if all(not board.get(pos) for pos in self.players_map[player_team]):
            if score[player_team] >= 5:
                score[player_team] -= 5
                for pos in self.players_map[player_team]:
                    board[pos].append(f"peasant_{player_team.lower()}")
                message = f"[RESTORE] Player {player_team} restored 5 peasants."
            else:
                message = f"[END] Player {player_team} does not have enough score to continue. LOSS."
                can_continue = False
        return can_continue, message

    def commit_action(self, action: Dict[str, Any]) -> tuple[list, list, bool]:
        pos, way = action.get("pos"), action.get("way")
        board_data, score_data, round_idx = self.game_state["board"], self.game_state["score"], self.game_state["round"]
        
        steps = []
        animation_events = []
        order = ["QA", "A1", "A2", "A3", "A4", "A5", "QB", "B5", "B4", "B3", "B2", "B1"]
        
        if not pos or not way or pos not in order or not board_data.get(pos):
            return [f"[error] Invalid move: {pos}"], [], False

        board, score = {k: v.copy() for k, v in board_data.items()}, score_data.copy()
        tokens = [t for t in board[pos] if not t.startswith("mandarin")]
        
        if not tokens: return [f"[error] No peasants to scatter from {pos}."], [], False

        animation_events.append({'type': 'pickup', 'pos': pos, 'pieces': tokens})
        board[pos] = [t for t in board[pos] if t.startswith("mandarin")]

        index, direction = order.index(pos), 1 if way == "left_to_right" else -1
        steps.append(f"[scatter] {pos} - {way.replace('_', ' ')}")

        current_pos_for_animation = pos
        for i, token in enumerate(tokens):
            target_index = (index + direction * (i + 1)) % len(order)
            target_pos = order[target_index]
            board[target_pos].append(token)
            animation_events.append({'type': 'drop', 'from_pos': current_pos_for_animation, 'to_pos': target_pos, 'piece': token})
            current_pos_for_animation = target_pos

        current_index = (index + direction * len(tokens)) % len(order)
        
        loop_count = 0
        while loop_count < 100:
            loop_count += 1
            next_index = (current_index + direction) % len(order)
            next_pos = order[next_index]

            if not board[next_pos]:
                next_next_index = (next_index + direction) % len(order)
                next_next_pos = order[next_next_index]
                
                if not board.get(next_next_pos): break
                
                if next_next_pos.startswith("Q"):
                    if len(board[next_next_pos]) < 5: break
                    if round_idx < 3: break
                
                if not board[next_next_pos]: break
                
                captured_pieces = board[next_next_pos]
                captured_team = "A" if captured_pieces[0].endswith("_a") else "B"
                animation_events.append({'type': 'capture', 'pos': next_next_pos, 'team': captured_team, 'pieces': captured_pieces})
                
                for token in captured_pieces:
                    value = 10 if token.startswith("mandarin") else 1
                    if token.endswith("_a"): score["A"] += value
                    else: score["B"] += value
                
                board[next_next_pos] = []
                animation_events.append({'type': 'score_update', 'score': score.copy()})
                current_index = next_next_index
            else:
                tokens_to_scatter = [t for t in board[next_pos] if not t.startswith("mandarin")]
                if not tokens_to_scatter: break
                
                animation_events.append({'type': 'pickup', 'pos': next_pos, 'pieces': tokens_to_scatter})
                board[next_pos] = [t for t in board[next_pos] if t.startswith("mandarin")]
                
                index = next_index
                current_pos_for_animation = next_pos
                for i, token in enumerate(tokens_to_scatter):
                    target_index = (index + direction * (i + 1)) % len(order)
                    target_pos = order[target_index]
                    board[target_pos].append(token)
                    animation_events.append({'type': 'drop', 'from_pos': current_pos_for_animation, 'to_pos': target_pos, 'piece': token})
                    current_pos_for_animation = target_pos
                current_index = (index + direction * len(tokens_to_scatter)) % len(order)

        self.game_state["board"], self.game_state["score"] = board, score
        
        is_end = not any(t.startswith("mandarin") for t in board["QA"]) and not any(t.startswith("mandarin") for t in board["QB"])
        if is_end:
            # Final sweep logic can be added here if needed
            pass

        return steps, animation_events, is_end


# =============================================================================
# SERVER (FastAPI)
# =============================================================================

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Game constants
MAX_ROUND_IN_GAME = 12
EARLY_WIN_SCORE = 25

# --- Models ---
class PlayerSettings(BaseModel):
    type: str
    model: Optional[str] = None
    temperature: Optional[float] = None
    maxTokens: Optional[int] = Field(None, alias='maxTokens')
    topP: Optional[float] = Field(None, alias='topP')
    thinkingMode: Optional[bool] = Field(None, alias='thinkingMode')

class GameSettings(BaseModel):
    player1: PlayerSettings
    player2: PlayerSettings

class HumanMove(BaseModel):
    pos: str
    way: str

# --- Global State ---
env = Enviroment()
p1 = MockPlayerAgent("A")
p2 = MockPlayerAgent("B")
current_turn = "A"
game_over = False
winner = None
game_settings = GameSettings(
    player1=PlayerSettings(type='agent'),
    player2=PlayerSettings(type='agent')
)


# --- Helper Function ---
def process_turn_end(end_reason, action, animation_events):
    global game_over, winner
    game_over = True
    score = env.get_game_state()["score"]
    
    if score["A"] > score["B"]: winner = "A"
    elif score["B"] > score["A"]: winner = "B"
    else: winner = "Draw"
    
    end_message = f"[GAME END] {end_reason}"
    if action.get("steps"): action["steps"].append(end_message)
    else: action["steps"] = [end_message]
    
    animation_events.append({'type': 'game_over', 'message': end_message, 'winner': winner})
    return action, animation_events

# --- API Endpoints ---
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.post("/api/settings")
async def apply_settings(settings: GameSettings):
    global game_settings
    game_settings = settings
    await reset_game()
    return {"message": "Settings applied successfully. Game has been reset.", "game_state": env.get_game_state(), "next_turn": current_turn, "game_over": False, "winner": None}

@app.post("/api/reset")
async def reset_game():
    global env, current_turn, game_over, winner
    env.reset()
    current_turn = "A"
    game_over = False
    winner = None
    return {"message": "Game has been reset!", "game_state": env.get_game_state(), "next_turn": current_turn, "game_over": False, "winner": None}

def run_move_logic(action):
    global current_turn
    steps, animation_events, is_end_by_capture = env.commit_action(action)
    action["steps"].extend(steps)
    
    score = env.get_game_state()["score"]
    end_reason = None
    if is_end_by_capture: end_reason = "Both Mandarins were captured."
    elif score["A"] >= EARLY_WIN_SCORE: end_reason = f"Player A reached {score['A']} points."
    elif score["B"] >= EARLY_WIN_SCORE: end_reason = f"Player B reached {score['B']} points."
    elif env.get_game_state()["round"] >= MAX_ROUND_IN_GAME: end_reason = f"Reached max round limit."
        
    if end_reason:
        action, animation_events = process_turn_end(end_reason, action, animation_events)
        
    if not game_over:
        current_turn = "B" if current_turn == "A" else "A"

    return {"action_details": action, "animation_events": animation_events, "game_over": game_over, "winner": winner, "next_turn": current_turn, "game_state": env.get_game_state()}


@app.post("/api/move")
async def request_move():
    if game_over: return {"game_over": True, "winner": winner, "game_state": env.get_game_state()}

    player_settings = game_settings.player1 if current_turn == 'A' else game_settings.player2
    
    if player_settings.type == 'human':
        available_pos = env.get_available_pos(current_turn)
        return {"human_turn": True, "team": current_turn, "available_pos": available_pos, "game_state": env.get_game_state()}

    if current_turn == "A": env.game_state["round"] += 1

    player = p1 if current_turn == "A" else p2
    action = {"steps": []}
    
    can_continue, restore_message = env.restore_peasants(player.team)
    if not can_continue:
        action, _ = process_turn_end(restore_message, action, [])
        return {"action_details": action, "game_over": True, "winner": winner, "game_state": env.get_game_state()}
    if restore_message: action["steps"].append(restore_message)

    available_pos = env.get_available_pos(player.team)
    current_action = player.get_action(env.get_game_state(), available_pos)
    action.update(current_action)

    if not action.get("pos"):
        action, _ = process_turn_end(f"Player {player.team} has no available moves.", action, [])
        return {"action_details": action, "game_over": True, "winner": winner, "game_state": env.get_game_state()}

    return run_move_logic(action)

@app.post("/api/human_move")
async def human_move(move: HumanMove):
    if game_over: return {"game_over": True, "winner": winner, "game_state": env.get_game_state()}
    if current_turn == "A": env.game_state["round"] += 1
    action = {"pos": move.pos, "way": move.way, "steps": []}
    return run_move_logic(action)

@app.get("/api/state")
async def get_state():
    return {"game_over": game_over, "winner": winner, "next_turn": current_turn, "game_state": env.get_game_state()}

