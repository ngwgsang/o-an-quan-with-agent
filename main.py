from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from core.environment import Enviroment
from core.player import MockPlayerAgent, PlayerAgent
from core.persona_instruct import ATTACKER, DEFENDER, BALANCED, STRATEGIC
from models.schemas import GameSettings, PlayerSettings, HumanMove
from core.endpoints import ENDPOINTS
from copy import deepcopy
import time
import os
import json
from datetime import datetime

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- Helper Function ---
def create_player_from_settings(team: str, settings: PlayerSettings):
    """Initializes a player agent based on the provided settings."""

    print("SETTING: ", settings)

    if settings.type == 'human':
        return None
    
    if settings.type == 'random_agent':
        return MockPlayerAgent(team=team, persona= BALANCED)

    if settings.type == 'agent':
        if not settings.model:
            settings.model = "gemini-2.0-flash-lite" 
        # Mặc định Balanced
        persona_obj = BALANCED
        if settings.persona:
            persona_map = {
                "ATTACK": ATTACKER,
                "DEFENSE": DEFENDER,
                "BALANCE": BALANCED,
                "STRATEGIC": STRATEGIC,
            }
            key = settings.persona.strip().upper()
            if key in persona_map:
                persona_obj = persona_map[key]
            else:
                print(f"Warning: Invalid persona value '{settings.persona}'. Using default 'BALANCED'.")

        
        model_provider = "google"
        for endpoint in ENDPOINTS:
            if endpoint["endpoint"] == settings.model:
                model_provider = endpoint["endpoint_provider"]
        
        
        return PlayerAgent(
            team=team,
            model=settings.model,
            provider=model_provider,
            temperature=settings.temperature,
            top_p=settings.topP,
            top_k=settings.topK,
            persona=persona_obj,
            mem_size=settings.memSize,
        )
    return None

# --- Global State ---
env = Enviroment()

game_settings = GameSettings(
    player1=PlayerSettings(type='agent', model='gemini-2.0-flash', temperature=0.7, maxTokens=50, topP=1.0, topK=40, memSize=5),
    player2=PlayerSettings(type='agent', model='gemini-2.0-flash', temperature=0.7, maxTokens=50, topP=1.0, topK=40, memSize=5)
)

p1 = create_player_from_settings("A", game_settings.player1)
p2 = create_player_from_settings("B", game_settings.player2)

print("SETTING 1: ", game_settings.player1)
print("SETTING 2: ", game_settings.player2)

current_turn = "A"
game_over = False
winner = None

MAX_ROUND_IN_GAME = 12
EARLY_WIN_SCORE = 25


# --- Structured JSON Log State ---
game_json_log = {
    "enviroment": {"special_rules": []},
    "setup": {
        "player_a": {},
        "player_b": {}
    },
    "result": None,
    "step_by_step": []
}
active_special_rules = set()
LOGS_DIR = "logs"
current_log_path = None


def _player_setup_from_settings(settings: PlayerSettings) -> dict:
    """Return a simplified view of player setup for logs.

    - For 'agent': keep configured endpoint and params (with BALANCED as default persona if empty).
    - For 'random_agent' or 'human': mark endpoint as the type and null all other fields.
    """
    if settings.type == 'agent':
        return {
            "endpoint": settings.model,
            "mem_size": settings.memSize,
            "persona": settings.persona if settings.persona else "BALANCED",
            "temp": settings.temperature,
            "top_p": settings.topP,
            "top_k": settings.topK,
            "max_token": settings.maxTokens,
        }

    # Non-LLM players: only indicate the kind; other params are irrelevant
    endpoint_label = settings.type if settings.type in ['random_agent', 'human'] else 'unknown'
    return {
        "endpoint": endpoint_label,
        "mem_size": None,
        "persona": None,
        "temp": None,
        "top_p": None,
        "top_k": None,
        "max_token": None,
    }


def init_game_log():
    global game_json_log, active_special_rules, current_log_path
    game_json_log = {
        "enviroment": {"special_rules": []},
        "setup": {
            "player_a": _player_setup_from_settings(game_settings.player1),
            "player_b": _player_setup_from_settings(game_settings.player2),
        },
        "result": None,
        "step_by_step": []
    }
    active_special_rules = set()
    ensure_logs_dir()
    current_log_path = make_new_log_filename()
    persist_game_log()


def ensure_logs_dir():
    try:
        os.makedirs(LOGS_DIR, exist_ok=True)
    except Exception:
        pass


def make_new_log_filename() -> str:
    ts = datetime.now().strftime("%Y.%m.%d.%H%M%S")
    return os.path.join(LOGS_DIR, f"report.{ts}.json")


def persist_game_log():
    global current_log_path
    try:
        if not current_log_path:
            ensure_logs_dir()
            current_log_path = make_new_log_filename()
        with open(current_log_path, "w", encoding="utf-8") as f:
            json.dump(game_json_log, f, ensure_ascii=False, indent=2)
    except Exception as e:
        # Best-effort logging; avoid crashing the app
        print("[log] persist error:", e)

# Do not create a log file at import time.
# A new log will be created on the first reset/apply_settings before a game starts.


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

def run_move_logic(move_payload, is_human_move: bool, extended_rule=None):
    """Runs the core logic for a single move and updates the game state."""
    global current_turn, game_over, winner
    global game_json_log, active_special_rules
    
    action_details = move_payload.copy()
    action_details["steps"] = action_details.get("steps", [])

    thoughts = action_details.pop('thoughts', [])

    move_action = move_payload.get("action", {})

    # track special rules used in this move and update environment log
    if extended_rule:
        for r in extended_rule:
            active_special_rules.add(r)
        game_json_log["enviroment"]["special_rules"] = sorted(list(active_special_rules))

    # Capture game state before action for logging
    before_state = deepcopy(env.get_game_state())

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
        
    player_settings = game_settings.player1 if current_turn == "A" else game_settings.player2
    
    show_dialog = (
        player_settings.type in ['agent', 'random_agent'] and 
        not is_human_move
    )

    # Build per-move structured log entry
    captured_peasants = 0
    captured_mandarin = 0
    scattering_step = 0
    for evt in animation_events:
        if evt.get('type') == 'capture':
            pieces = evt.get('pieces', [])
            captured_peasants += sum(1 for t in pieces if isinstance(t, str) and t.startswith('peasant'))
            captured_mandarin += sum(1 for t in pieces if isinstance(t, str) and t.startswith('mandarin'))
        if evt.get('type') == 'drop':
            scattering_step += 1

    after_state = deepcopy(env.get_game_state())
    reasoning_secs = move_payload.get('_meta_reasoning_secs', 0)

    step_log = {
        "observation": move_payload.get("observation", ""),
        "reason": move_payload.get("reason", ""),
        "action": [move_action.get("pos"), move_action.get("way")],
        "reasoning_times": reasoning_secs,
        "round": before_state.get("round"),
        "my_score": after_state.get("score", {}).get(current_turn),
        "game_state_before_act": before_state,
        "game_state_after_act": after_state,
        "captured_peasant": captured_peasants,
        "captured_mandarin": captured_mandarin,
        "scattering_step": scattering_step,
    }
    game_json_log["step_by_step"].append(step_log)
    persist_game_log()

    if not game_over:
        current_turn = "B" if current_turn == "A" else "A"

    # Update result section if game over
    if game_over:
        score = after_state.get("score", {})
        if winner == 'A':
            game_json_log["result"] = {"winner": "player_a", "score": [score.get('A', 0), score.get('B', 0)], "final_round": after_state.get("round")}
        elif winner == 'B':
            game_json_log["result"] = {"winner": "player_b", "score": [score.get('B', 0), score.get('A', 0)], "final_round": after_state.get("round")}
        else:
            game_json_log["result"] = {"winner": "draw", "score": [score.get('A', 0), score.get('B', 0)], "final_round": after_state.get("round")}
        persist_game_log()

    return {
        "action_details": action_details, 
        "animation_events": animation_events, 
        "game_over": game_over, 
        "winner": winner, 
        "next_turn": current_turn, 
        "game_state": env.get_game_state(), 
        "thoughts": thoughts,
        "move_by_human": is_human_move,
        "show_thinking_dialog": show_dialog
    }


# --- API Endpoints ---
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api/endpoints")
async def get_endpoints():
    return ENDPOINTS

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
    init_game_log()
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
    start_t = time.perf_counter()
    move_payload = player.get_action(env.get_game_state(), available_pos, extended_rule=extended_rule)
    end_t = time.perf_counter()
    move_payload['_meta_reasoning_secs'] = round(end_t - start_t, 6)
    move_payload['team'] = player.team
    move_payload["steps"] = steps

    if not move_payload.get("action", {}).get("pos"):
        action_details, _ = process_turn_end(f"Player {player.team} has no available moves.", move_payload, [])
        return {"action_details": action_details, "game_over": True, "winner": winner, "game_state": env.get_game_state()}

    return run_move_logic(move_payload, is_human_move=False, extended_rule=extended_rule)

@app.post("/api/human_move")
async def human_move(move: HumanMove):
    if game_over: return {"game_over": True, "winner": winner, "game_state": env.get_game_state()}
    if current_turn == "A": env.game_state["round"] += 1
    
    move_payload = {
        "reason": "Human action",
        "action": {
            "pos": move.pos,
            "way": move.way
        },
        "extended_rule": move.extended_rule,
        "observation": "",
        "_meta_reasoning_secs": 0.0,
        "team": current_turn
    }
    return run_move_logic(move_payload, is_human_move=True, extended_rule=move.extended_rule)

@app.get("/api/state")
async def get_state():
    return {"game_over": game_over, "winner": winner, "next_turn": current_turn, "game_state": env.get_game_state()}

@app.get("/api/export_json")
async def export_json():
    """Return the structured JSON game log as a downloadable file."""
    persist_game_log()
    if not current_log_path or not os.path.exists(current_log_path):
        # Fallback to return JSON in-memory if file not created
        return game_json_log
    filename = os.path.basename(current_log_path)
    return FileResponse(
        current_log_path,
        media_type="application/json",
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
