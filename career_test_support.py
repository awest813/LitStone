"""Shared helpers for career E2E tests (API + browser)."""

from game_logic import CAMPAIGN_NODES, create_player

CHAPTER_NAMES = [n["name"] for n in CAMPAIGN_NODES]
TOTAL_CHAPTERS = len(CAMPAIGN_NODES)


def mage_deck() -> list[str]:
    return create_player("P", "Mage", shuffle=False)["deck"]


def is_campaign_node_unlocked(node_id: str, completed: list[str], nodes: list[dict]) -> bool:
    """Mirror static/game.js isCampaignNodeUnlocked()."""
    idx = next(i for i, n in enumerate(nodes) if n["id"] == node_id)
    if idx <= 0:
        return True
    return nodes[idx - 1]["id"] in completed


def mark_campaign_victory(node_id: str, completed: list[str]) -> list[str]:
    """Mirror static/game.js onCampaignVictory() progress update."""
    if node_id not in completed:
        completed.append(node_id)
    return completed


def is_career_complete(completed: list[str], total_chapters: int = TOTAL_CHAPTERS) -> bool:
    """Mirror static/game.js isCareerComplete()."""
    return len(completed) >= total_chapters


def setup_lethal_turn(gs: dict) -> None:
    """Give the player a guaranteed lethal attack on the enemy hero."""
    p1, p2 = gs["p1"], gs["p2"]
    p1["board"] = [{
        "name": "Charge Bruiser",
        "type": "minion",
        "cost": 5,
        "atk": 15,
        "hp": 1,
        "max_hp": 1,
        "can_attack": True,
        "charge": True,
    }]
    p1["hand"] = []
    p1["mana"] = 10
    p1["max_mana"] = 10
    p1["hero_power_used"] = False
    p2["hp"] = 10
    p2["board"] = []
    gs["is_player_turn"] = True
