"""
test_career_playthrough.py — End-to-end career flow via the Flask API.

Simulates the full client journey:
  hub → career map (/api/campaign) → each chapter (new game, mulligan, win)
  → all six chapters cleared including three boss duels.
"""

import unittest

from game_logic import (
    BOSS_PRESETS,
    CAMPAIGN_NODES,
    DECK_SIZE,
    complete_deck_from_core,
    create_player,
)
from server import GAMES, app

EXPECTED_CHAPTERS = [
    {"id": "n1", "name": "Street Urchin", "ai_class": "Rogue", "difficulty": "easy"},
    {"id": "n2", "name": "Town Guard", "ai_class": "Warrior", "difficulty": "normal"},
    {"id": "n3", "name": "Guild Librarian", "ai_class": "Mage", "difficulty": "normal"},
    {"id": "n4", "name": "Victor Frankenstein", "boss_id": "frankenstein", "difficulty": "hard"},
    {"id": "n5", "name": "Van Helsing", "boss_id": "van_helsing", "difficulty": "hard"},
    {"id": "n6", "name": "Professor Moriarty", "boss_id": "moriarty", "difficulty": "hard"},
]


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


def is_career_complete(completed: list[str], total_chapters: int = 6) -> bool:
    """Mirror static/game.js isCareerComplete()."""
    return len(completed) >= total_chapters


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


def _play_career_chapter(client, deck: list[str], node: dict) -> dict:
    """Start a career duel, mulligan, win, and return final state."""
    node_id = node["id"]
    start = client.post("/api/new_game", json={
        "hero_class": "Mage",
        "deck": deck,
        "campaign_node": node_id,
    })
    assert start.status_code == 200, start.get_json()
    data = start.get_json()
    gid = data["game_id"]

    mull = client.post("/api/mulligan", json={"game_id": gid, "indices": []})
    assert mull.status_code == 200, mull.get_json()

    _setup_lethal_turn(GAMES[gid])
    win = client.post("/api/action", json={
        "game_id": gid,
        "action": "attack",
        "idx": 0,
        "target": "hero",
    })
    assert win.status_code == 200, win.get_json()
    assert win.get_json()["winner"] == "Player"
    return win.get_json()


class TestCareerPlaythrough(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.deck = _mage_deck()
        self.assertEqual(len(self.deck), DECK_SIZE)
        GAMES.clear()

    def test_hub_page_loads(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn("screen-hub", html)
        self.assertIn("Career", html)
        self.assertIn("goToCareer", html)
        self.assertIn("screen-campaign", html)
        self.assertNotIn("5 chapter", html.lower())

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

    def test_career_api_metadata_for_all_chapters(self):
        """Mirror goToCampaign() — load map with opponent HP/class for every node."""
        res = self.client.get("/api/campaign")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["total_chapters"], 6)
        self.assertEqual(data["deck_size"], DECK_SIZE)
        nodes = data["nodes"]
        self.assertEqual(len(nodes), 6)

        for expected in EXPECTED_CHAPTERS:
            node = next(n for n in nodes if n["id"] == expected["id"])
            self.assertEqual(node["name"], expected["name"])
            self.assertEqual(node["difficulty"], expected["difficulty"])
            if "boss_id" in expected:
                self.assertEqual(node["boss_id"], expected["boss_id"])
                boss = BOSS_PRESETS[expected["boss_id"]]
                self.assertEqual(node["opponent_name"], boss["display_name"])
                self.assertEqual(node["opponent_class"], boss["hero_class"])
                self.assertEqual(node["opponent_hp"], boss["hp"])
            else:
                self.assertEqual(node["opponent_class"], expected["ai_class"])
                self.assertEqual(node["opponent_hp"], 30)

    def test_full_career_start_to_finish(self):
        """Hub → six chapters → career complete. Each duel: new game, mulligan, lethal win."""
        camp = self.client.get("/api/campaign")
        self.assertEqual(camp.status_code, 200)
        camp_data = camp.get_json()
        nodes = camp_data["nodes"]
        self.assertEqual(len(nodes), 6)
        self.assertEqual(camp_data["total_chapters"], 6)
        self.assertEqual([n["id"] for n in nodes], [n["id"] for n in CAMPAIGN_NODES])

        completed: list[str] = []
        for i, node in enumerate(nodes):
            node_id = node["id"]
            self.assertTrue(
                is_campaign_node_unlocked(node_id, completed, nodes),
                f"{node_id} should be unlocked with progress {completed}",
            )
            self.assertFalse(is_career_complete(completed))

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
            self.assertIn("card_db", data)
            self.assertIn("desc_short", data["card_db"]["Quill Bolt"])

            if node.get("boss_id"):
                self.assertEqual(data["boss_id"], node["boss_id"])
                boss = BOSS_PRESETS[node["boss_id"]]
                self.assertEqual(data["opponent_name"], boss["display_name"])
                self.assertEqual(data["p2"]["hero_class"], boss["hero_class"])
                self.assertEqual(data["p2"]["hp"], boss["hp"])
            else:
                self.assertIsNone(data.get("boss_id"))
                self.assertEqual(data["p2"]["hero_class"], node["ai_class"])

            career_log = next(
                (line for line in data["log"] if line.startswith("--- Career:")),
                None,
            )
            self.assertIsNotNone(career_log)
            self.assertIn(node["name"], career_log)

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
            if i < len(nodes) - 1:
                self.assertFalse(is_career_complete(completed))
            else:
                self.assertTrue(is_career_complete(completed))

        self.assertEqual(completed, [n["id"] for n in nodes])
        self.assertEqual(completed[-1], "n6")

    def test_each_boss_chapter_opponent_setup(self):
        """Boss chapters n4–n6 use scripted decks and hero HP from BOSS_PRESETS."""
        boss_nodes = [n for n in EXPECTED_CHAPTERS if "boss_id" in n]
        self.assertEqual([n["id"] for n in boss_nodes], ["n4", "n5", "n6"])

        for expected in boss_nodes:
            start = self.client.post("/api/new_game", json={
                "hero_class": "Mage",
                "deck": self.deck,
                "campaign_node": expected["id"],
            })
            self.assertEqual(start.status_code, 200)
            data = start.get_json()
            preset = BOSS_PRESETS[expected["boss_id"]]
            self.assertEqual(data["boss_id"], expected["boss_id"])
            self.assertEqual(data["opponent_name"], preset["display_name"])
            self.assertEqual(data["p2"]["hero_class"], preset["hero_class"])
            self.assertEqual(data["p2"]["hp"], preset["hp"])
            gid = data["game_id"]
            p2 = GAMES[gid]["p2"]
            self.assertEqual(len(p2["deck"]) + len(p2["hand"]), DECK_SIZE)
            self.assertEqual(
                len(complete_deck_from_core(preset["hero_class"], preset["core"])),
                DECK_SIZE,
            )

    def test_career_progress_unlocks_all_six_sequentially(self):
        """Winning each chapter unlocks exactly the next — no skips."""
        camp = self.client.get("/api/campaign").get_json()
        nodes = camp["nodes"]
        completed: list[str] = []

        for node in nodes:
            for locked in nodes:
                if locked["id"] == node["id"]:
                    continue
                should_unlock = is_campaign_node_unlocked(locked["id"], completed, nodes)
                if nodes.index(locked) < nodes.index(node):
                    self.assertTrue(should_unlock, f"{locked['id']} should be unlocked before {node['id']}")
                elif nodes.index(locked) > nodes.index(node):
                    self.assertFalse(should_unlock, f"{locked['id']} should stay locked before {node['id']}")

            _play_career_chapter(self.client, self.deck, node)
            completed = mark_campaign_victory(node["id"], completed)

        self.assertTrue(is_career_complete(completed))
        self.assertEqual(len(completed), 6)

    def test_campaign_victory_unlocks_next_chapter_immediately(self):
        """Mirrors client: beating n1 should unlock n2 before overlay re-render."""
        completed: list[str] = []
        nodes = self.client.get("/api/campaign").get_json()["nodes"]
        start = self.client.post("/api/new_game", json={
            "hero_class": "Mage",
            "deck": self.deck,
            "campaign_node": "n1",
        })
        gid = start.get_json()["game_id"]
        self.client.post("/api/mulligan", json={"game_id": gid, "indices": []})
        _setup_lethal_turn(GAMES[gid])
        self.client.post("/api/action", json={
            "game_id": gid,
            "action": "attack",
            "idx": 0,
            "target": "hero",
        })
        completed = mark_campaign_victory("n1", completed)
        self.assertTrue(is_campaign_node_unlocked("n2", completed, nodes))
        self.assertFalse(is_campaign_node_unlocked("n3", completed, nodes))

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
