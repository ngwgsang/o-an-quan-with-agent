from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from core.environment import Enviroment
from core.player import MockPlayerAgent, PlayerAgent
from models.schemas import GameSettings, PlayerSettings, HumanMove
from core.config import ALL_ENDPOINTS

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- Helper Function ---
def create_player_from_settings(team: str, settings: PlayerSettings):
    """Initializes a player agent based on the provided settings."""
    if settings.type == 'human':
        return None
    
    if settings.type == 'random_agent':
        return MockPlayerAgent(team=team)

    if settings.type == 'agent':
        # Default to a flash model if none is provided
        if not settings.model:
            settings.model = "gemini-2.0-flash-lite" 
        
        return PlayerAgent(
            team=team,
            model=settings.model,
            temperature=settings.temperature,
            top_p=settings.topP,
            top_k=settings.topK
        )
    return None

# --- Global State ---
env = Enviroment()

# Default player settings
game_settings = GameSettings(
    player1=PlayerSettings(type='agent', model='gemini-2.0-flash', temperature=0.7, maxTokens=50, topP=1.0, topK=40),
    player2=PlayerSettings(type='agent', model='gemini-2.0-flash', temperature=0.7, maxTokens=50, topP=1.0, topK=40)
)

# Initialize players based on default settings
p1 = create_player_from_settings("A", game_settings.player1)
p2 = create_player_from_settings("B", game_settings.player2)

current_turn = "A"
game_over = False
winner = None

# Game constants
MAX_ROUND_IN_GAME = 12
EARLY_WIN_SCORE = 25


def process_turn_end(end_reason, action_details, animation_events):
    """Processes the end of a turn, checking for game-over conditions."""
    global game_over, winner
    game_over = True
    score = env.get_game_state()["score"]
    
    if score["A"] > score["B"]: winner = "A"
    elif score["B"] > score["A"]: winner = "B"
    else: winner = "Draw"
    
    end_message = f"[GAME END] {end_reason}"
    if action_details.get("steps"):
        action_details["steps"].append(end_message)
    else:
        action_details["steps"] = [end_message]
    
    animation_events.append({'type': 'game_over', 'message': end_message, 'winner': winner})
    return action_details, animation_events

def run_move_logic(move_payload, extended_rule=None):
    """Runs the core logic for a single move and updates the game state."""
    global current_turn, game_over, winner
    
    action_details = move_payload.copy()
    action_details["steps"] = action_details.get("steps", [])

    move_action = move_payload.get("action", {})
    steps, animation_events, is_end_by_capture = env.commit_action(move_action, extended_rule)
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

@app.get("/api/endpoints")
async def get_endpoints():
    return ALL_ENDPOINTS

@app.post("/api/settings")
async def apply_settings(settings: GameSettings):
    global game_settings, p1, p2
    game_settings = settings
    p1 = create_player_from_settings("A", game_settings.player1)
    p2 = create_player_from_settings("B", game_settings.player2)
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
async def request_move(request: Request):
    if game_over: return {"game_over": True, "winner": winner, "game_state": env.get_game_state()}

    try:
        body = await request.json()
    except Exception:
        body = {}
    extended_rule = body.get("extended_rule")

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

    return run_move_logic(move_payload, extended_rule)

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
    return run_move_logic(move_payload, move.extended_rule)

@app.get("/api/state")
async def get_state():
    return {"game_over": game_over, "winner": winner, "next_turn": current_turn, "game_state": env.get_game_state()}
