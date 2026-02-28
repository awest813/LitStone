"""
game_logic.py — Pure Python game logic for TinyStone.
No Tkinter/GUI dependencies. All emoji replaced with text codes
so log entries render safely in any environment.
"""

import random

# ---------------------------------------------------------------------------
# 1. CARD DATABASE & CONFIGURATION
# ---------------------------------------------------------------------------

CARD_DB = {
    "Peasant": {"type": "minion", "cost": 1, "atk": 2, "hp": 1, "taunt": False, "icon": "PE"},
    "Guard":   {"type": "minion", "cost": 2, "atk": 2, "hp": 3, "taunt": True,  "icon": "GD"},
    "Raider":  {"type": "minion", "cost": 3, "atk": 4, "hp": 2, "taunt": False, "icon": "RD"},
    "Knight":  {"type": "minion", "cost": 3, "atk": 3, "hp": 1, "charge": True, "icon": "KN"},
    "Paladin": {"type": "minion", "cost": 4, "atk": 3, "hp": 3, "taunt": True,  "divine_shield": True, "icon": "PA"},
    "Dragon":  {"type": "minion", "cost": 5, "atk": 5, "hp": 6, "taunt": False, "icon": "DR"},
    "Spider":  {"type": "minion", "cost": 2, "atk": 1, "hp": 2, "poisonous": True, "icon": "SP"},
    "Cleric":  {"type": "minion", "cost": 2, "atk": 2, "hp": 2, "battlecry": {"effect": "heal_hero", "val": 3}, "icon": "CL"},
    "Bomber":  {"type": "minion", "cost": 2, "atk": 1, "hp": 1, "deathrattle": {"effect": "dmg_hero", "val": 2}, "icon": "BM"},
    "Zap":     {"type": "spell",  "cost": 2, "effect": "damage",     "val": 3, "icon": "ZP"},
    "Blast":   {"type": "spell",  "cost": 4, "effect": "damage",     "val": 6, "icon": "BL"},
    "Mend":    {"type": "spell",  "cost": 3, "effect": "heal",       "val": 5, "icon": "MD"},
    "Insight": {"type": "spell",  "cost": 3, "effect": "draw",       "val": 2, "icon": "IN"},
    "Cleave":  {"type": "spell",  "cost": 4, "effect": "damage_all", "val": 2, "icon": "CV"},
    "Blessing":{"type": "spell",  "cost": 2, "effect": "buff",       "val": [2, 2], "icon": "BS"},
    "Axe":     {"type": "weapon", "cost": 3, "atk": 3, "durability": 2, "icon": "AX"},
}

HERO_CLASSES = ["Mage", "Warrior", "Priest"]
HERO_ICONS   = {"Mage": "MG", "Warrior": "WR", "Priest": "PR"}

KW_COLORS = {
    "taunt": "#E74C3C", "divine_shield": "#F1C40F", "charge": "#2ECC71",
    "poisonous": "#9B59B6", "battlecry": "#3498DB", "deathrattle": "#566573",
}
KW_SHORT = [("taunt","TAUNT"),("divine_shield","SHIELD"),("charge","CHARGE"),
            ("poisonous","POISON"),("battlecry","B.CRY"),("deathrattle","D.RATTLE")]
KW_LONG  = [("taunt","TAUNT"),("divine_shield","DIVINE SHIELD"),("charge","CHARGE"),
            ("poisonous","POISONOUS"),("battlecry","BATTLECRY"),("deathrattle","DEATHRATTLE")]

GAME_LOG: list[str] = []


def get_spell_desc(card: dict, short: bool = False) -> str:
    e, v = card.get("effect"), card.get("val")
    if e == "damage":     return f"Deal {v} Dmg"            if short else f"Deal {v} damage."
    if e == "heal":       return f"Heal {v} HP"             if short else f"Restore {v} HP."
    if e == "draw":       return f"Draw {v} Cards"          if short else f"Draw {v} cards."
    if e == "damage_all": return f"AoE Dmg {v}"             if short else f"Deal {v} dmg to all enemies."
    if e == "buff":       return f"Buff +{v[0]}/+{v[1]}"   if short else f"Give a minion +{v[0]}/+{v[1]}."
    return ""


def log_action(msg: str) -> None:
    GAME_LOG.append(msg)


# ---------------------------------------------------------------------------
# 2. STATE INITIALISATION
# ---------------------------------------------------------------------------

def create_player(name: str, hero_class: str = "Mage",
                  custom_deck: list | None = None, shuffle: bool = True) -> dict:
    if custom_deck is not None:
        deck = custom_deck.copy()
    else:
        deck = []
        pool = list(CARD_DB.keys())
        while len(deck) < 15:
            c = random.choice(pool)
            if deck.count(c) < 2:
                deck.append(c)
    if shuffle:
        random.shuffle(deck)
    return {
        "name":            name,
        "hero_class":      hero_class,
        "hp":              30,
        "armor":           0,
        "mana":            0,
        "max_mana":        0,
        "deck":            deck,
        "hand":            [],
        "board":           [],
        "fatigue":         0,
        "hero_power_used": False,
        "weapon":          None,
        "hero_can_attack": False,
    }


def draw_card(player: dict, on_event=None) -> None:
    if player["deck"]:
        if len(player["hand"]) < 10:
            player["hand"].append(player["deck"].pop(0))
        else:
            burned = player["deck"].pop(0)
            log_action(f"{player['name']}'s hand is full! {burned} is burned.")
    else:
        player["fatigue"] += 1
        damage_hero(player, player["fatigue"])
        log_action(f"FATIGUE! {player['name']} takes {player['fatigue']} damage.")
        if on_event:
            on_event("damage", player, "hero", player["fatigue"])


def start_turn(player: dict, on_event=None) -> None:
    if player["max_mana"] < 10:
        player["max_mana"] += 1
    player["mana"] = player["max_mana"]
    player["hero_power_used"] = False
    player["hero_can_attack"] = bool(player["weapon"])
    for m in player["board"]:
        m["can_attack"] = True
    draw_card(player, on_event)


# ---------------------------------------------------------------------------
# 3. CORE RULES & LOGIC
# ---------------------------------------------------------------------------

def damage_hero(player: dict, amount: int) -> None:
    if amount <= 0:
        return
    if player.get("armor", 0) > 0:
        if amount <= player["armor"]:
            player["armor"] -= amount
            return
        amount -= player["armor"]
        player["armor"] = 0
    player["hp"] -= amount


def get_valid_targets(opp: dict, is_attack: bool = True) -> list:
    if is_attack:
        taunt = [i for i, m in enumerate(opp["board"]) if m.get("taunt")]
        if taunt:
            return taunt
    return ["hero"] + list(range(len(opp["board"])))


def get_legal_moves(player: dict, opp: dict) -> list:
    moves = []

    for hand_idx, card_name in enumerate(player["hand"]):
        card = CARD_DB[card_name]
        if player["mana"] < card["cost"]:
            continue
        if card["type"] == "minion":
            if len(player["board"]) < 7:
                moves.append(("play", hand_idx, None))
        elif card["type"] == "spell":
            if card["effect"] in ("heal", "draw", "damage_all"):
                moves.append(("play", hand_idx, None))
            elif card["effect"] == "damage":
                for t in get_valid_targets(opp, is_attack=False):
                    moves.append(("play", hand_idx, t))
            elif card["effect"] == "buff":
                for t in range(len(player["board"])):
                    moves.append(("play", hand_idx, t))
        elif card["type"] == "weapon":
            moves.append(("play", hand_idx, None))

    valid_targets = get_valid_targets(opp, is_attack=True)
    for bi, minion in enumerate(player["board"]):
        if minion.get("can_attack"):
            for t in valid_targets:
                moves.append(("attack", bi, t))

    if player["weapon"] and player["hero_can_attack"]:
        for t in valid_targets:
            moves.append(("hero_attack", None, t))

    if player["mana"] >= 2 and not player["hero_power_used"]:
        cls = player["hero_class"]
        if cls == "Warrior":
            moves.append(("hero_power", None, None))
        elif cls == "Mage":
            for t in get_valid_targets(opp, is_attack=False):
                moves.append(("hero_power", None, t))
        elif cls == "Priest":
            for t in ["hero"] + list(range(len(player["board"]))):
                moves.append(("hero_power", None, t))

    return moves


def execute_move(player: dict, opp: dict, move: tuple, on_event=None) -> None:
    action, idx, target = move

    def notify(e_type, tp, ti, amt):
        if on_event:
            on_event(e_type, tp, ti, amt)

    # ---- PLAY ---------------------------------------------------------------
    if action == "play":
        card_name = player["hand"].pop(idx)
        card = CARD_DB[card_name]
        player["mana"] -= card["cost"]
        log_action(f">> {player['name']} plays {card_name}!")
        notify("play", player, None, card_name)

        if card["type"] == "minion":
            minion = card.copy()
            minion["name"]       = card_name
            minion["max_hp"]     = card["hp"]
            minion["can_attack"] = card.get("charge", False)
            player["board"].append(minion)
            if "battlecry" in card:
                bc = card["battlecry"]
                if bc["effect"] == "heal_hero":
                    amt = max(0, min(bc["val"], 30 - player["hp"]))
                    player["hp"] += amt
                    log_action(f"   [B.CRY] Battlecry: Heals hero for {amt}!")
                    notify("heal", player, "hero", amt)

        elif card["type"] == "weapon":
            player["weapon"] = {"name": card_name, "atk": card["atk"],
                                 "durability": card["durability"]}
            player["hero_can_attack"] = True
            log_action(f"   Equipped {card_name} ({card['atk']} Atk / {card['durability']} Durability).")

        elif card["type"] == "spell":
            if card["effect"] == "heal":
                amt = max(0, min(card["val"], 30 - player["hp"]))
                player["hp"] += amt
                log_action(f"   {player['name']} heals for {amt} HP.")
                notify("heal", player, "hero", amt)

            elif card["effect"] == "draw":
                log_action(f"   {player['name']} draws {card['val']} cards!")
                for _ in range(card["val"]):
                    draw_card(player, on_event)

            elif card["effect"] == "damage_all":
                log_action(f"   Deals {card['val']} damage to all enemy minions!")
                for i, tm in enumerate(opp["board"]):
                    if tm.get("divine_shield") and card["val"] > 0:
                        tm["divine_shield"] = False
                        log_action(f"   Divine Shield protects {tm['name']}!")
                        notify("blocked", opp, i, "BLOCKED!")
                    else:
                        tm["hp"] -= card["val"]
                        notify("damage", opp, i, card["val"])

            elif card["effect"] == "buff":
                tm = player["board"][target]
                tm["atk"]    += card["val"][0]
                tm["hp"]     += card["val"][1]
                tm["max_hp"]  = tm.get("max_hp", tm["hp"]) + card["val"][1]
                log_action(f"   {player['name']} buffs {tm['name']} by +{card['val'][0]}/+{card['val'][1]}!")
                notify("heal", player, target, card["val"][1])

            elif card["effect"] == "damage":
                if target == "hero":
                    damage_hero(opp, card["val"])
                    log_action(f"   Deals {card['val']} damage to {opp['name']}!")
                    notify("damage", opp, "hero", card["val"])
                else:
                    tm = opp["board"][target]
                    if tm.get("divine_shield") and card["val"] > 0:
                        tm["divine_shield"] = False
                        log_action(f"   Divine Shield protects {tm['name']}!")
                        notify("blocked", opp, target, "BLOCKED!")
                    else:
                        tm["hp"] -= card["val"]
                        log_action(f"   Deals {card['val']} damage to {tm['name']}.")
                        notify("damage", opp, target, card["val"])

    # ---- ATTACK -------------------------------------------------------------
    elif action == "attack":
        attacker = player["board"][idx]
        attacker["can_attack"] = False

        if target == "hero":
            damage_hero(opp, attacker["atk"])
            log_action(f">> {attacker['name']} attacks {opp['name']} for {attacker['atk']} damage!")
            notify("damage", opp, "hero", attacker["atk"])
        else:
            defender = opp["board"][target]
            log_action(f">> {attacker['name']} attacks {defender['name']}!")

            if defender.get("divine_shield"):
                defender["divine_shield"] = False
                log_action(f"   {defender['name']}'s Divine Shield blocks the attack!")
                notify("blocked", opp, target, "BLOCKED!")
            else:
                defender["hp"] -= attacker["atk"]
                notify("damage", opp, target, attacker["atk"])
                if attacker.get("poisonous") and attacker["atk"] > 0:
                    defender["hp"] = 0
                    log_action(f"   [POISON] Poisonous destroys {defender['name']}!")

            if attacker.get("divine_shield"):
                attacker["divine_shield"] = False
                log_action(f"   {attacker['name']}'s Divine Shield blocks retaliation!")
                notify("blocked", player, idx, "BLOCKED!")
            else:
                attacker["hp"] -= defender["atk"]
                notify("damage", player, idx, defender["atk"])
                if defender.get("poisonous") and defender["atk"] > 0:
                    attacker["hp"] = 0
                    log_action(f"   [POISON] Poisonous destroys {attacker['name']}!")

    # ---- HERO ATTACK --------------------------------------------------------
    elif action == "hero_attack":
        player["hero_can_attack"] = False
        weapon = player["weapon"]
        w_atk  = weapon["atk"]

        if target == "hero":
            damage_hero(opp, w_atk)
            log_action(f">> {player['name']} attacks {opp['name']} with {weapon['name']} for {w_atk} dmg!")
            notify("damage", opp, "hero", w_atk)
        else:
            defender = opp["board"][target]
            log_action(f">> {player['name']} attacks {defender['name']} with {weapon['name']}!")
            if defender.get("divine_shield"):
                defender["divine_shield"] = False
                log_action(f"   {defender['name']}'s Divine Shield blocks the attack!")
                notify("blocked", opp, target, "BLOCKED!")
            else:
                defender["hp"] -= w_atk
                notify("damage", opp, target, w_atk)
            damage_hero(player, defender["atk"])
            notify("damage", player, "hero", defender["atk"])

        weapon["durability"] -= 1
        if weapon["durability"] <= 0:
            log_action(f"   {player['name']}'s {weapon['name']} breaks!")
            player["weapon"] = None

    # ---- HERO POWER ---------------------------------------------------------
    elif action == "hero_power":
        player["mana"] -= 2
        player["hero_power_used"] = True
        cls = player["hero_class"]

        if cls == "Warrior":
            player["armor"] += 2
            log_action(f">> {player['name']} uses Armor Up! Gains 2 Armor.")
            notify("armor", player, "hero", 2)

        elif cls == "Mage":
            if target == "hero":
                damage_hero(opp, 1)
                log_action(f">> {player['name']} uses Fireblast! Deals 1 damage to {opp['name']}.")
                notify("damage", opp, "hero", 1)
            else:
                tm = opp["board"][target]
                if tm.get("divine_shield"):
                    tm["divine_shield"] = False
                    log_action(f">> {player['name']} uses Fireblast! Divine Shield blocks it.")
                    notify("blocked", opp, target, "BLOCKED!")
                else:
                    tm["hp"] -= 1
                    log_action(f">> {player['name']} uses Fireblast! Deals 1 damage to {tm['name']}.")
                    notify("damage", opp, target, 1)

        elif cls == "Priest":
            if target == "hero":
                amt = max(0, min(2, 30 - player["hp"]))
                player["hp"] += amt
                log_action(f">> {player['name']} uses Lesser Heal! Restores {amt} HP to {player['name']}.")
                notify("heal", player, "hero", amt)
            else:
                tm = player["board"][target]
                max_hp = tm.get("max_hp", tm["hp"])
                amt = max(0, min(2, max_hp - tm["hp"]))
                tm["hp"] += amt
                log_action(f">> {player['name']} uses Lesser Heal! Restores {amt} HP to {tm['name']}.")
                notify("heal", player, target, amt)

    cleanup_dead(player, opp, on_event)


def cleanup_dead(player: dict, opp: dict, on_event=None) -> None:
    def process(owner, enemy):
        alive = []
        for m in owner["board"]:
            if m["hp"] > 0:
                alive.append(m)
            else:
                if "deathrattle" in m:
                    dr = m["deathrattle"]
                    if dr["effect"] == "dmg_hero":
                        damage_hero(enemy, dr["val"])
                        log_action(f"   [D.RATTLE] {m['name']} Deathrattle: Deals {dr['val']} dmg to {enemy['name']}!")
                        if on_event:
                            on_event("damage", enemy, "hero", dr["val"])
        return alive

    player["board"] = process(player, opp)
    opp["board"]    = process(opp, player)


def check_win(p1: dict, p2: dict) -> str | None:
    if p1["hp"] <= 0 and p2["hp"] <= 0:
        return "DRAW"
    if p1["hp"] <= 0:
        return p2["name"]
    if p2["hp"] <= 0:
        return p1["name"]
    return None


# ---------------------------------------------------------------------------
# 4. AI
# ---------------------------------------------------------------------------

def evaluate_ai_move(p2: dict, p1: dict, move: tuple) -> float:
    action, idx, target = move
    score = 0.0

    p1_eff_hp = p1["hp"] + p1.get("armor", 0)
    p2_eff_hp = p2["hp"] + p2.get("armor", 0)

    if action == "play":
        card_name = p2["hand"][idx]
        card = CARD_DB[card_name]
        score += card["cost"] * 2

        if card["type"] == "minion":
            score += 3
            if card.get("poisonous"): score += 2
            if card.get("charge"):    score += 2
            if "battlecry" in card:
                bc = card["battlecry"]
                if bc["effect"] == "heal_hero" and p2["hp"] < 25:
                    score += 3

        elif card["type"] == "weapon":
            score += card["atk"] * 2 if not p2["weapon"] else -4

        elif card["type"] == "spell":
            if card["effect"] == "damage":
                if target != "hero":
                    tm = p1["board"][target]
                    if tm.get("divine_shield"):  score += 3
                    elif tm["hp"] <= card["val"]: score += 6
                    else:                         score += 2
                else:
                    if p1_eff_hp <= card["val"]: score += 1000
                    score += 1

            elif card["effect"] == "heal":
                score += 5 if p2["hp"] < 15 else -5

            elif card["effect"] == "draw":
                score += card["val"] * 4 if len(p2["hand"]) < 9 else -10

            elif card["effect"] == "damage_all":
                hits = sum(5 if m["hp"] <= card["val"] else 1 for m in p1["board"])
                score += hits * 2 if hits else -10

            elif card["effect"] == "buff":
                score += sum(card["val"]) * 2
                tm = p2["board"][target]
                if tm["can_attack"]: score += card["val"][0] * 3
                if tm["hp"] > 2:     score += 2

    elif action == "attack":
        attacker = p2["board"][idx]
        if target == "hero":
            if p1_eff_hp <= attacker["atk"]: score += 1000
            score += attacker["atk"]
        else:
            defender = p1["board"][target]
            atk_dmg = 0 if defender.get("divine_shield") else attacker["atk"]
            if atk_dmg > 0 and attacker.get("poisonous"): atk_dmg = defender["hp"]
            def_dmg = 0 if attacker.get("divine_shield") else defender["atk"]
            if def_dmg > 0 and defender.get("poisonous"): def_dmg = attacker["hp"]

            if def_dmg < attacker["hp"] and atk_dmg >= defender["hp"]: score += 15
            elif atk_dmg >= defender["hp"]:                              score += 5
            else:                                                         score -= 5

    elif action == "hero_attack":
        w_atk = p2["weapon"]["atk"]
        if target == "hero":
            if p1_eff_hp <= w_atk: score += 1000
            score += w_atk
        else:
            defender = p1["board"][target]
            atk_dmg = 0 if defender.get("divine_shield") else w_atk
            def_dmg = defender["atk"]
            if def_dmg >= p2_eff_hp:   score -= 1000
            elif atk_dmg >= defender["hp"]:
                score += 6
                score -= def_dmg
            else:
                score -= 5

    elif action == "hero_power":
        cls = p2["hero_class"]
        if cls == "Warrior":
            score += 2
        elif cls == "Mage":
            if target != "hero":
                tm = p1["board"][target]
                if tm.get("divine_shield"): score += 4
                elif tm["hp"] == 1:         score += 12
                else:                       score += 1
            else:
                if p1_eff_hp <= 1: score += 1000
                score += 1
        elif cls == "Priest":
            if target == "hero":
                score += 3 if p2["hp"] <= 28 else -5
            else:
                tm = p2["board"][target]
                max_hp = tm.get("max_hp", tm["hp"])
                score += 4 if tm["hp"] < max_hp else -5

    return score


def run_ai_turn(p2: dict, p1: dict, max_moves: int = 10) -> list[tuple]:
    """Execute AI turn synchronously. Returns the list of moves made."""
    start_turn(p2)
    moves_made = []
    for _ in range(max_moves):
        if check_win(p1, p2):
            break
        legal = get_legal_moves(p2, p1)
        if not legal:
            break
        best, best_score = None, -9999.0
        for mv in legal:
            s = evaluate_ai_move(p2, p1, mv) + random.uniform(0, 0.5)
            if s > best_score:
                best_score, best = s, mv
        if best_score < 0:
            break
        execute_move(p2, p1, best)
        moves_made.append(best)
    return moves_made
