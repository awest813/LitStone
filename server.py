"""
server.py — Flask web server for LitStone.
Serves the browser-based UI and exposes a JSON REST API for all game actions.
"""

import os
import random
import uuid

from flask import Flask, jsonify, render_template, request
from whitenoise import WhiteNoise

from game_logic import (
    CARD_DB,
    DECK_SIZE,
    GAME_LOG,
    HERO_CLASSES,
    OPENING_HAND_FIRST,
    OPENING_HAND_SECOND,
    ai_do_mulligan,
    card_allowed_for_class,
    cards_for_class,
    check_win,
    create_player,
    do_mulligan,
    draw_card,
    execute_move,
    get_legal_moves,
    give_coin,
    log_action,
    run_ai_turn,
    set_active_log,
    start_turn,
)

app = Flask(__name__)

_static_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.wsgi_app = WhiteNoise(app.wsgi_app, root=_static_root, prefix="static/")

# ---------------------------------------------------------------------------
# Per-session game state (keyed by game_id UUID)
# ---------------------------------------------------------------------------
GAMES: dict[str, dict] = {}


def _resolve_game_id() -> str | None:
    data = request.get_json(silent=True) or {}
    gid = (data.get("game_id") or request.args.get("game_id") or "").strip()
    return gid or None


def _get_game(game_id: str | None) -> dict | None:
    if not game_id:
        return None
    return GAMES.get(game_id)


def _validate_deck(deck: list, hero_class: str) -> bool:
    if hero_class not in HERO_CLASSES:
        return False
    pool = set(cards_for_class(hero_class))
    return (
        isinstance(deck, list) and
        len(deck) == DECK_SIZE and
        all(c in pool for c in deck) and
        all(card_allowed_for_class(c, hero_class) for c in deck) and
        all(deck.count(c) <= (1 if CARD_DB[c].get("legendary") else 2) for c in deck)
    )


def _serialize(player: dict) -> dict:
    """Return a JSON-safe copy of a player dict."""
    p = dict(player)
    p["board"] = [dict(m) for m in player["board"]]
    return p


def _serialize_opponent(player: dict) -> dict:
    """Return a JSON-safe copy of an opponent player dict with hidden information masked."""
    p = _serialize(player)
    p["hand"] = ["?"] * len(player["hand"])
    p["deck"] = ["?"] * len(player["deck"])
    return p


def _state_response(gs: dict, *, include_card_db: bool = False) -> dict:
    winner = check_win(gs["p1"], gs["p2"])
    mulligan = gs.get("mulligan_phase", False)
    legal = get_legal_moves(gs["p1"], gs["p2"]) if not winner and not mulligan else []
    resp = {
        "game_id":          gs["game_id"],
        "p1":               _serialize(gs["p1"]),
        "p2":               _serialize_opponent(gs["p2"]),
        "is_player_turn":   gs.get("is_player_turn", True),
        "player_goes_first": gs.get("player_goes_first", True),
        "turn_number":      gs.get("turn_number", 1),
        "log":              list(gs.get("log", [])[-60:]),
        "winner":           winner,
        "_legal_moves":     legal,
        "mulligan_phase":   mulligan,
    }
    if include_card_db:
        resp["card_db"] = CARD_DB
    return resp


def _with_game_log(gs: dict):
    """Context manager helper — activate per-game logging for rule engine calls."""
    class _LogCtx:
        def __enter__(self):
            set_active_log(gs.setdefault("log", []))
            return gs

        def __exit__(self, *args):
            set_active_log(None)

    return _LogCtx()


def _deal_opening_hands(gs: dict) -> None:
    """Deal opening hands based on who goes first."""
    first, second = (gs["p1"], gs["p2"]) if gs["player_goes_first"] else (gs["p2"], gs["p1"])
    for _ in range(OPENING_HAND_FIRST):
        draw_card(first)
    for _ in range(OPENING_HAND_SECOND):
        draw_card(second)


def _finish_mulligan(gs: dict) -> None:
    """AI mulligan, grant The Coin, and begin the first turn."""
    ai_do_mulligan(gs["p2"])

    if gs["player_goes_first"]:
        give_coin(gs["p2"])
    else:
        give_coin(gs["p1"])

    gs["mulligan_phase"] = False

    if gs["player_goes_first"]:
        gs["is_player_turn"] = True
        gs["turn_number"] = 1
        start_turn(gs["p1"], draw=False)
        log_action("--- Your Turn (Turn 1) ---")
        return

    gs["is_player_turn"] = False
    gs["turn_number"] = 1
    log_action("--- AI goes first ---")
    run_ai_turn(gs["p2"], gs["p1"], draw=False)
    winner = check_win(gs["p1"], gs["p2"])
    if winner:
        log_action(f"=== {winner} wins! ===")
        return
    gs["is_player_turn"] = True
    gs["turn_number"] = 2
    start_turn(gs["p1"])
    log_action("--- Your Turn (Turn 2) ---")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html", card_db=CARD_DB, hero_classes=HERO_CLASSES)


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "heroes": len(HERO_CLASSES), "deck_size": DECK_SIZE})


@app.route("/api/cards", methods=["GET"])
def cards():
    """Return the card database and hero class list — available before any game starts."""
    collectibles = {k: v for k, v in CARD_DB.items() if not v.get("uncollectible")}
    return jsonify({
        "card_db": collectibles,
        "hero_classes": HERO_CLASSES,
        "deck_size": DECK_SIZE,
    })


@app.route("/api/new_game", methods=["POST"])
def new_game():
    data       = request.get_json() or {}
    player_cls = data.get("hero_class", "Mage")
    deck       = data.get("deck", [])

    if player_cls not in HERO_CLASSES:
        player_cls = "Mage"

    if not _validate_deck(deck, player_cls):
        return jsonify({
            "error": f"Invalid deck — need {DECK_SIZE} legal cards for {player_cls} (neutrals + class cards only).",
        }), 400

    game_id = str(uuid.uuid4())
    GAME_LOG.clear()

    player_goes_first = random.choice([True, False])
    gs = {
        "game_id":           game_id,
        "p1":                create_player("Player", player_cls, deck),
        "p2":                create_player("AI", random.choice(HERO_CLASSES)),
        "turn_number":       1,
        "is_player_turn":    True,
        "mulligan_phase":    True,
        "player_goes_first": player_goes_first,
        "log":               [],
    }
    GAMES[game_id] = gs

    with _with_game_log(gs):
        log_action("--- NEW GAME STARTED ---")
        order = "You go first." if player_goes_first else "AI goes first — you'll receive The Coin."
        log_action(order)
        _deal_opening_hands(gs)
        log_action("--- Mulligan Phase: choose cards to replace ---")

    return jsonify(_state_response(gs, include_card_db=True))


@app.route("/api/mulligan", methods=["POST"])
def do_mulligan_route():
    game_id = _resolve_game_id()
    gs = _get_game(game_id)
    if not gs:
        return jsonify({"error": "No game in progress"}), 400
    if not gs.get("mulligan_phase"):
        return jsonify({"error": "Not in mulligan phase"}), 400

    data    = request.get_json() or {}
    indices = data.get("indices", [])
    if not isinstance(indices, list):
        indices = []
    indices = [i for i in indices if isinstance(i, int) and 0 <= i < len(gs["p1"]["hand"])]

    with _with_game_log(gs):
        do_mulligan(gs["p1"], indices)
        _finish_mulligan(gs)

    return jsonify(_state_response(gs, include_card_db=True))


@app.route("/api/state", methods=["GET"])
def get_state():
    game_id = _resolve_game_id()
    gs = _get_game(game_id)
    if not gs:
        return jsonify({"error": "No game in progress"}), 400
    return jsonify(_state_response(gs))


@app.route("/api/action", methods=["POST"])
def do_action():
    game_id = _resolve_game_id()
    gs = _get_game(game_id)
    if not gs:
        return jsonify({"error": "No game in progress"}), 400

    p1 = gs["p1"]
    p2 = gs["p2"]

    if gs.get("mulligan_phase"):
        return jsonify({"error": "Mulligan phase in progress"}), 400

    if not gs.get("is_player_turn"):
        return jsonify({"error": "Not your turn"}), 400

    data   = request.get_json() or {}
    action = data.get("action")
    idx    = data.get("idx")
    target = data.get("target")

    if isinstance(target, int):
        pass
    elif target == "hero":
        pass
    else:
        target = None

    with _with_game_log(gs):
        if action == "end_turn":
            gs["is_player_turn"] = False
            log_action("--- AI's Turn ---")
            run_ai_turn(p2, p1)
            gs["turn_number"] += 1
            winner = check_win(p1, p2)
            if not winner:
                gs["is_player_turn"] = True
                start_turn(p1)
                log_action(f"--- Your Turn (Turn {gs['turn_number']}) ---")
            else:
                log_action(f"=== {winner} wins! ===")
            return jsonify(_state_response(gs))

        move  = (action, idx, target)
        legal = get_legal_moves(p1, p2)
        if move not in legal:
            return jsonify({"error": "Illegal move", "legal": legal}), 400

        execute_move(p1, p2, move)

        winner = check_win(p1, p2)
        if winner:
            log_action(f"=== {winner} wins! ===")

    return jsonify(_state_response(gs))


@app.route("/api/legal_moves", methods=["GET"])
def legal_moves():
    game_id = _resolve_game_id()
    gs = _get_game(game_id)
    if not gs:
        return jsonify({"error": "No game in progress"}), 400
    moves = get_legal_moves(gs["p1"], gs["p2"])
    return jsonify({"moves": moves})


@app.route("/api/resign", methods=["POST"])
def resign():
    """Remove a game session so a new match can start cleanly."""
    game_id = _resolve_game_id()
    if game_id and game_id in GAMES:
        del GAMES[game_id]
    if not GAMES:
        GAME_LOG.clear()
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "").lower() in ("1", "true", "yes")
    print("LitStone server starting — open http://localhost:5000 in your browser.")
    app.run(debug=debug, port=5000)
