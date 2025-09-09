#!/usr/bin/env python3
"""
Basic CLI runner to auto-play games via the FastAPI server
and generate structured logs without using the web UI.

Usage examples:
  - Run 1 game with random agents (fast, no API calls):
      python -m cli.run_basic --p1-type random_agent --p2-type random_agent

  - Run 3 games using Gemini models:
      python -m cli.run_basic --games 3 \
          --p1-type agent --p1-model gemini-2.0-flash \
          --p2-type agent --p2-model gemini-2.0-flash-lite

  - Download the final JSON log for each game to local folder:
      python -m cli.run_basic --download-logs --out-dir logs/exported

Server defaults to http://127.0.0.1:8000 (must be running).
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from typing import Any, Dict, List, Optional

import requests


def _print(msg: str) -> None:
    print(msg, flush=True)


def check_server(base_url: str, timeout: float = 3.0) -> bool:
    try:
        r = requests.get(f"{base_url}/api/state", timeout=timeout)
        return r.status_code == 200
    except Exception:
        return False


def post_json(base_url: str, path: str, payload: dict | None = None, timeout: float = 30.0) -> dict:
    url = f"{base_url}{path}"
    r = requests.post(url, json=payload or {}, timeout=timeout)
    r.raise_for_status()
    return r.json()


def get_json(base_url: str, path: str, timeout: float = 30.0) -> dict:
    url = f"{base_url}{path}"
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.json()


def fetch_and_save_log(base_url: str, out_dir: str) -> Optional[str]:
    """Downloads the current JSON log via /api/export_json.

    Returns the saved file path (or None if failed).
    """
    url = f"{base_url}/api/export_json"
    try:
        with requests.get(url, stream=True, timeout=60.0) as r:
            if r.status_code != 200:
                return None
            filename = None
            dispo = r.headers.get("Content-Disposition", "")
            # Content-Disposition: attachment; filename=report.2025.01.01.120000.json
            if "filename=" in dispo:
                filename = dispo.split("filename=")[-1].strip().strip('"')
            if not filename:
                filename = f"report.{int(time.time())}.json"

            os.makedirs(out_dir, exist_ok=True)
            save_path = os.path.join(out_dir, filename)
            with open(save_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            return save_path
    except Exception:
        return None


def build_player_settings(
    p_type: str,
    model: Optional[str],
    temperature: Optional[float],
    max_tokens: Optional[int],
    top_p: Optional[float],
    top_k: Optional[int],
    persona: Optional[str],
    mem_size: Optional[int],
) -> Dict[str, Any]:
    """Build settings payload for the server.

    For 'agent' include model and sampling params. For 'random_agent' or 'human',
    only send the type to avoid polluting logs with unused fields.
    """
    data: Dict[str, Any] = {"type": p_type}
    if p_type == "agent":
        if model is not None:
            data["model"] = model
        if temperature is not None:
            data["temperature"] = temperature
        if max_tokens is not None:
            data["maxTokens"] = max_tokens
        if top_p is not None:
            data["topP"] = top_p
        if top_k is not None:
            data["topK"] = top_k
        if persona is not None:
            data["persona"] = persona
        if mem_size is not None:
            data["memSize"] = mem_size
    return data


def run_single_game(
    base_url: str,
    p1_settings: Dict[str, Any],
    p2_settings: Dict[str, Any],
    extended_rules: Optional[List[str]] = None,
    print_steps: bool = True,
) -> Dict[str, Any]:
    """Runs a single game until completion via the HTTP API."""

    # Apply settings (server already performs a reset inside /api/settings)
    state = post_json(base_url, "/api/settings", {"player1": p1_settings, "player2": p2_settings})
    game_over = state.get("game_over", False)

    # Safety in case server returns immediate game over
    if game_over:
        return state

    move_idx = 0
    start_ts = time.time()
    while True:
        move_idx += 1
        payload = {"extended_rule": extended_rules} if extended_rules else {}
        resp = post_json(base_url, "/api/move", payload)

        if print_steps:
            team = resp.get("next_turn", "?")
            a = resp.get("action_details", {}).get("steps", [])
            if a:
                _print(f"[step {move_idx:02d}] {a[-1]}")

        if resp.get("game_over", False):
            end_ts = time.time()
            result = {
                "winner": resp.get("winner"),
                "elapsed_secs": round(end_ts - start_ts, 3),
                "final_state": resp.get("game_state", {}),
            }
            return result


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Auto-play O An Quan games via API")
    p.add_argument("--server", default="http://127.0.0.1:8000", help="Base URL of FastAPI server")
    p.add_argument("--games", type=int, default=1, help="Number of games to run")
    p.add_argument("--extended-rules", nargs="*", default=None, help="Optional extended rules list, e.g. E1 E2 E3")
    p.add_argument("--quiet", action="store_true", help="Reduce console output")
    p.add_argument("--download-logs", action="store_true", help="Download final JSON log after each game")
    p.add_argument("--out-dir", default="logs/exported", help="Where to save downloaded logs")

    # Player 1 settings
    p.add_argument("--p1-type", default="agent", choices=["agent", "random_agent", "human"], help="Player 1 type")
    p.add_argument("--p1-model", default="gemini-2.0-flash", help="Player 1 model/endpoint")
    p.add_argument("--p1-temp", type=float, default=0.7, help="Player 1 temperature")
    p.add_argument("--p1-top-p", type=float, default=1.0, help="Player 1 top_p")
    p.add_argument("--p1-top-k", type=int, default=40, help="Player 1 top_k")
    p.add_argument("--p1-persona", default=None, help="Player 1 persona (ATTACK|DEFENSE|BALANCE|STRATEGIC)")
    p.add_argument("--p1-mem", type=int, default=3, help="Player 1 memory size")
    p.add_argument("--p1-max-tokens", type=int, default=256, help="Player 1 max tokens")

    # Player 2 settings
    p.add_argument("--p2-type", default="agent", choices=["agent", "random_agent", "human"], help="Player 2 type")
    p.add_argument("--p2-model", default="gemini-2.0-flash", help="Player 2 model/endpoint")
    p.add_argument("--p2-temp", type=float, default=0.7, help="Player 2 temperature")
    p.add_argument("--p2-top-p", type=float, default=1.0, help="Player 2 top_p")
    p.add_argument("--p2-top-k", type=int, default=40, help="Player 2 top_k")
    p.add_argument("--p2-persona", default=None, help="Player 2 persona (ATTACK|DEFENSE|BALANCE|STRATEGIC)")
    p.add_argument("--p2-mem", type=int, default=3, help="Player 2 memory size")
    p.add_argument("--p2-max-tokens", type=int, default=256, help="Player 2 max tokens")

    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    base_url = args.server.rstrip("/")

    if not check_server(base_url):
        _print(f"Server not reachable at {base_url}. Please start FastAPI (e.g., `uvicorn main:app --reload`).")
        return 2

    p1 = build_player_settings(
        p_type=args.p1_type,
        model=args.p1_model,
        temperature=args.p1_temp,
        max_tokens=args.p1_max_tokens,
        top_p=args.p1_top_p,
        top_k=args.p1_top_k,
        persona=args.p1_persona,
        mem_size=args.p1_mem,
    )
    p2 = build_player_settings(
        p_type=args.p2_type,
        model=args.p2_model,
        temperature=args.p2_temp,
        max_tokens=args.p2_max_tokens,
        top_p=args.p2_top_p,
        top_k=args.p2_top_k,
        persona=args.p2_persona,
        mem_size=args.p2_mem,
    )

    if p1.get("type") == "human" or p2.get("type") == "human":
        _print("Human player type is not supported by this CLI. Use agent or random_agent.")
        return 3

    _print(f"Running {args.games} game(s) against {base_url}...")
    for gi in range(1, args.games + 1):
        _print(f"\n=== Game {gi}/{args.games} ===")
        res = run_single_game(base_url, p1, p2, extended_rules=args.extended_rules, print_steps=(not args.quiet))
        _print(f"Result: winner={res.get('winner')}, elapsed={res.get('elapsed_secs')}s")

        if args.download_logs:
            saved = fetch_and_save_log(base_url, args.out_dir)
            if saved:
                _print(f"Saved JSON log: {saved}")
            else:
                _print("Could not download JSON log (server may not expose a file).")

    _print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
