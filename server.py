"""
server.py — Flask web server for LitStone.
Serves the browser-based UI and exposes a JSON REST API for all game actions.
"""

import random
from flask import Flask, jsonify, request, render_template

from game_logic import (
    CARD_DB, HERO_CLASSES, GAME_LOG,
    create_player, draw_card, start_turn, do_mulligan,
    get_legal_moves, execute_move, check_win,
    run_ai_turn, log_action,
)

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Single-session game state (one game at a time — fine for a local demo)
# ---------------------------------------------------------------------------
GAME_STATE: dict = {}


def _serialize(player: dict) -> dict:
    """Return a JSON-safe copy of a player dict."""
    p = dict(player)
    p["board"] = [dict(m) for m in player["board"]]
    return p


def _state_response() -> dict:
    gs = GAME_STATE
    winner = check_win(gs["p1"], gs["p2"]) if gs else None
    mulligan = gs.get("mulligan_phase", False)
    legal  = get_legal_moves(gs["p1"], gs["p2"]) if gs and not winner and not mulligan else []
    return {
        "p1":             _serialize(gs["p1"]),
        "p2":             _serialize(gs["p2"]),
        "is_player_turn": gs.get("is_player_turn", True),
        "turn_number":    gs.get("turn_number", 1),
        "log":            list(GAME_LOG[-60:]),
        "winner":         winner,
        "card_db":        CARD_DB,
        "_legal_moves":   legal,
        "mulligan_phase": mulligan,
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html", card_db=CARD_DB, hero_classes=HERO_CLASSES)


@app.route("/api/cards", methods=["GET"])
def cards():
    """Return the card database and hero class list — available before any game starts."""
    return jsonify({"card_db": CARD_DB, "hero_classes": HERO_CLASSES})


@app.route("/api/new_game", methods=["POST"])
def new_game():
    data       = request.get_json()
    player_cls = data.get("hero_class", "Mage")
    deck       = data.get("deck", [])

    # Sanitise inputs
    if player_cls not in HERO_CLASSES:
        player_cls = "Mage"

    valid_cards = set(CARD_DB.keys())
    deck_valid  = (
        isinstance(deck, list) and
        len(deck) == 15 and
        all(c in valid_cards for c in deck) and
        all(deck.count(c) <= (1 if CARD_DB[c].get("legendary") else 2) for c in deck)
    )

    GAME_LOG.clear()
    log_action("--- NEW GAME STARTED ---")

    ai_class = random.choice(HERO_CLASSES)
    gs = GAME_STATE
    gs["p1"] = create_player("Player", player_cls, deck if deck_valid else None)
    gs["p2"] = create_player("AI", ai_class)

    # Deal opening hands (mulligan phase — player sees these before game begins)
    for _ in range(3):
        draw_card(gs["p1"])
    for _ in range(4):
        draw_card(gs["p2"])

    gs["turn_number"]    = 1
    gs["is_player_turn"] = True
    gs["mulligan_phase"] = True
    log_action("--- Mulligan Phase: choose cards to replace ---")

    return jsonify(_state_response())


@app.route("/api/mulligan", methods=["POST"])
def do_mulligan_route():
    if not GAME_STATE:
        return jsonify({"error": "No game in progress"}), 400
    gs = GAME_STATE
    if not gs.get("mulligan_phase"):
        return jsonify({"error": "Not in mulligan phase"}), 400

    data    = request.get_json()
    indices = data.get("indices", [])
    if not isinstance(indices, list):
        indices = []
    # Validate indices
    indices = [i for i in indices if isinstance(i, int) and 0 <= i < len(gs["p1"]["hand"])]

    do_mulligan(gs["p1"], indices)
    gs["mulligan_phase"] = False
    start_turn(gs["p1"])
    log_action("--- Your Turn (Turn 1) ---")

    return jsonify(_state_response())


@app.route("/api/state", methods=["GET"])
def get_state():
    if not GAME_STATE:
        return jsonify({"error": "No game in progress"}), 400
    return jsonify(_state_response())


@app.route("/api/action", methods=["POST"])
def do_action():
    if not GAME_STATE:
        return jsonify({"error": "No game in progress"}), 400

    gs  = GAME_STATE
    p1  = gs["p1"]
    p2  = gs["p2"]

    if gs.get("mulligan_phase"):
        return jsonify({"error": "Mulligan phase in progress"}), 400

    if not gs.get("is_player_turn"):
        return jsonify({"error": "Not your turn"}), 400

    data   = request.get_json()
    action = data.get("action")
    idx    = data.get("idx")      # None is fine for hero actions
    target = data.get("target")   # May be "hero" or an int index

    # Normalise target type (JSON sends numbers as int, "hero" as string)
    if isinstance(target, int):
        pass  # already correct
    elif target == "hero":
        pass
    else:
        target = None

    if action == "end_turn":
        gs["is_player_turn"] = False
        log_action("--- AI's Turn ---")
        run_ai_turn(p2, p1)
        gs["turn_number"] += 1
        # Only start the player's turn if nobody has won
        winner = check_win(p1, p2)
        if not winner:
            gs["is_player_turn"] = True
            start_turn(p1)
            log_action(f"--- Your Turn (Turn {gs['turn_number']}) ---")
        return jsonify(_state_response())

    # Validate and execute player move
    move   = (action, idx, target)
    legal  = get_legal_moves(p1, p2)
    if move not in legal:
        return jsonify({"error": "Illegal move", "legal": legal}), 400

    execute_move(p1, p2, move)

    winner = check_win(p1, p2)
    if winner:
        log_action(f"=== {winner} wins! ===")

    return jsonify(_state_response())


@app.route("/api/legal_moves", methods=["GET"])
def legal_moves():
    if not GAME_STATE:
        return jsonify({"error": "No game in progress"}), 400
    gs = GAME_STATE
    moves = get_legal_moves(gs["p1"], gs["p2"])
    return jsonify({"moves": moves})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("LitStone server starting — open http://localhost:5000 in your browser.")
    app.run(debug=True, port=5000)
