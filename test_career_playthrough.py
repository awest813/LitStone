"""
test_career_playthrough.py — End-to-end career flow via the Flask API.

Simulates: hub → campaign list → each node (new game, mulligan, win) → career complete.
"""

import unittest

from game_logic import BOSS_PRESETS, CAMPAIGN_NODES, create_player
from server import GAMES, app


def _mage_deck() -> list[str]:
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


def _setup_lethal_turn(gs: dict) -> None:
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


class TestCareerPlaythrough(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.deck = _mage_deck()
        GAMES.clear()

    def test_hub_page_loads(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn("screen-hub", html)
        self.assertIn("Career", html)
        self.assertIn("goToCareer", html)

    def test_campaign_unlock_order_matches_client(self):
        completed: list[str] = []
        nodes = CAMPAIGN_NODES
        self.assertTrue(is_campaign_node_unlocked("n1", completed, nodes))
        for node in nodes[1:]:
            self.assertFalse(
                is_campaign_node_unlocked(node["id"], completed, nodes),
                f"{node['id']} should stay locked until prior node is cleared",
            )
        completed = mark_campaign_victory("n1", completed)
        self.assertTrue(is_campaign_node_unlocked("n2", completed, nodes))

    def test_full_career_start_to_finish(self):
        camp = self.client.get("/api/campaign")
        self.assertEqual(camp.status_code, 200)
        nodes = camp.get_json()["nodes"]
        self.assertEqual(len(nodes), 5)
        self.assertEqual([n["id"] for n in nodes], [n["id"] for n in CAMPAIGN_NODES])

        completed: list[str] = []
        for node in nodes:
            node_id = node["id"]
            self.assertTrue(
                is_campaign_node_unlocked(node_id, completed, nodes),
                f"{node_id} should be unlocked with progress {completed}",
            )

            start = self.client.post("/api/new_game", json={
                "hero_class": "Mage",
                "deck": self.deck,
                "campaign_node": node_id,
            })
            self.assertEqual(start.status_code, 200, start.get_json())
            data = start.get_json()
            gid = data["game_id"]

            self.assertEqual(data["mode"], "campaign")
            self.assertEqual(data["campaign_node"], node_id)
            self.assertEqual(data["ai_difficulty"], node["difficulty"])
            self.assertTrue(data["mulligan_phase"])

            if node.get("boss_id"):
                self.assertEqual(data["boss_id"], node["boss_id"])
                boss = BOSS_PRESETS[node["boss_id"]]
                self.assertEqual(data["opponent_name"], boss["display_name"])
                self.assertEqual(data["p2"]["hero_class"], boss["hero_class"])
            else:
                self.assertIsNone(data.get("boss_id"))
                self.assertEqual(data["p2"]["hero_class"], node["ai_class"])

            mull = self.client.post("/api/mulligan", json={"game_id": gid, "indices": []})
            self.assertEqual(mull.status_code, 200)
            self.assertFalse(mull.get_json()["mulligan_phase"])

            _setup_lethal_turn(GAMES[gid])
            win = self.client.post("/api/action", json={
                "game_id": gid,
                "action": "attack",
                "idx": 0,
                "target": "hero",
            })
            self.assertEqual(win.status_code, 200, win.get_json())
            self.assertEqual(win.get_json()["winner"], "Player")

            completed = mark_campaign_victory(node_id, completed)

        self.assertEqual(completed, [n["id"] for n in nodes])

    def test_career_nodes_reject_invalid_id(self):
        res = self.client.post("/api/new_game", json={
            "hero_class": "Mage",
            "deck": self.deck,
            "campaign_node": "n99",
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn("error", res.get_json())


if __name__ == "__main__":
    unittest.main(verbosity=2)
