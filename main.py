from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from core.environment import Enviroment
from core.player import MockPlayerAgent
from models.schemas import GameSettings, PlayerSettings, HumanMove

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

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
# Game constants
MAX_ROUND_IN_GAME = 12
EARLY_WIN_SCORE = 25

# --- Helper Function ---
def process_turn_end(end_reason, action_details, animation_events):
    global game_over, winner
    game_over = True
    score = env.get_game_state()["score"]
    
    if score["A"] > score["B"]: winner = "A"
    elif score["B"] > score["A"]: winner = "B"
    else: winner = "Draw"
    
    end_message = f"[GAME END] {end_reason}"
    if action_details.get("steps"): action_details["steps"].append(end_message)
    else: action_details["steps"] = [end_message]
    
    animation_events.append({'type': 'game_over', 'message': end_message, 'winner': winner})
    return action_details, animation_events

def run_move_logic(move_payload):
    global current_turn, game_over, winner
    
    action_details = move_payload.copy()
    action_details["steps"] = action_details.get("steps", [])

    move_action = move_payload.get("action", {})
    steps, animation_events, is_end_by_capture = env.commit_action(move_action)
    action_details["steps"].extend(steps)
    
    score = env.get_game_state()["score"]
    end_reason = None
    if is_end_by_capture: end_reason = "Both Mandarins were captured."
    elif score["A"] >= EARLY_WIN_SCORE: end_reason = f"Player A reached {score['A']} points."
    elif score["B"] >= EARLY_WIN_SCORE: end_reason = f"Player B reached {score['B']} points."
    elif env.get_game_state()["round"] >= MAX_ROUND_IN_GAME: end_reason = f"Reached max round limit."
        
    if end_reason:
        action_details, animation_events = process_turn_end(end_reason, action_details, animation_events)
        
    if not game_over:
        current_turn = "B" if current_turn == "A" else "A"

    return {"action_details": action_details, "animation_events": animation_events, "game_over": game_over, "winner": winner, "next_turn": current_turn, "game_state": env.get_game_state()}


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

@app.post("/api/move")
async def request_move():
    if game_over: return {"game_over": True, "winner": winner, "game_state": env.get_game_state()}

    player_settings = game_settings.player1 if current_turn == 'A' else game_settings.player2
    
    if player_settings.type == 'human':
        available_pos = env.get_available_pos(current_turn)
        return {"human_turn": True, "team": current_turn, "available_pos": available_pos, "game_state": env.get_game_state()}

    if current_turn == "A": env.game_state["round"] += 1

    player = p1 if current_turn == "A" else p2
    
    action_details = {}
    steps = []

    can_continue, restore_message = env.restore_peasants(player.team)
    if not can_continue:
        action_details, _ = process_turn_end(restore_message, {}, [])
        return {"action_details": action_details, "game_over": True, "winner": winner, "game_state": env.get_game_state()}
    if restore_message: steps.append(restore_message)

    available_pos = env.get_available_pos(player.team)
    move_payload = player.get_action(env.get_game_state(), available_pos)
    move_payload["steps"] = steps

    if not move_payload.get("action", {}).get("pos"):
        action_details, _ = process_turn_end(f"Player {player.team} has no available moves.", move_payload, [])
        return {"action_details": action_details, "game_over": True, "winner": winner, "game_state": env.get_game_state()}

    return run_move_logic(move_payload)

@app.post("/api/human_move")
async def human_move(move: HumanMove):
    if game_over: return {"game_over": True, "winner": winner, "game_state": env.get_game_state()}
    if current_turn == "A": env.game_state["round"] += 1
    
    move_payload = {
        "reason": "Human action",
        "action": {
            "pos": move.pos,
            "way": move.way
        }
    }
    return run_move_logic(move_payload)

@app.get("/api/state")
async def get_state():
    return {"game_over": game_over, "winner": winner, "next_turn": current_turn, "game_state": env.get_game_state()}