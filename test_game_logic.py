"""
test_game_logic.py — Unit tests for LitStone game_logic.py

Run with:  python -m pytest test_game_logic.py -v
       or:  python test_game_logic.py
"""

import sys
import random
import unittest

# Ensure the game_logic module is importable from this directory.
sys.path.insert(0, ".")

from game_logic import (
    CARD_DB, HERO_CLASSES, GAME_LOG,
    create_player, draw_card, start_turn, do_mulligan,
    get_legal_moves, execute_move, check_win,
    run_ai_turn, log_action, damage_hero, get_valid_targets,
    cleanup_dead, evaluate_ai_move,
)


def _make_minion(name, atk, hp, **kwargs):
    """Helper: create a minimal board minion dict."""
    m = {"name": name, "type": "minion", "cost": 1, "atk": atk, "hp": hp,
         "max_hp": hp, "can_attack": True, **kwargs}
    return m


class TestCreatePlayer(unittest.TestCase):
    def test_defaults(self):
        p = create_player("P1", "Mage")
        self.assertEqual(p["name"], "P1")
        self.assertEqual(p["hero_class"], "Mage")
        self.assertEqual(p["hp"], 30)
        self.assertEqual(p["armor"], 0)
        self.assertEqual(p["mana"], 0)
        self.assertEqual(p["max_mana"], 0)
        self.assertEqual(len(p["deck"]), 15)
        self.assertEqual(p["hand"], [])
        self.assertEqual(p["board"], [])
        self.assertFalse(p["hero_power_used"])
        self.assertIsNone(p["weapon"])
        self.assertFalse(p["hero_can_attack"])

    def test_custom_deck_used(self):
        deck = ["Town Crier"] * 2 + ["Castle Guard"] * 2 + ["Highwayman"] * 2 + \
               ["Errant Knight"] * 2 + ["Storybook Dragon"] * 2 + \
               ["Quill Bolt"] * 2 + ["Inferno Verse"] * 1 + \
               ["Restorative Hymn"] * 1 + ["Deductive Clue"] * 1
        self.assertEqual(len(deck), 15)
        p = create_player("P1", "Rogue", custom_deck=deck, shuffle=False)
        self.assertEqual(p["deck"], deck)

    def test_all_hero_classes(self):
        for cls in HERO_CLASSES:
            p = create_player("P", cls)
            self.assertEqual(p["hero_class"], cls)


class TestDrawCard(unittest.TestCase):
    def setUp(self):
        GAME_LOG.clear()

    def test_normal_draw(self):
        p = create_player("P1", "Mage")
        self.assertEqual(len(p["deck"]), 15)
        draw_card(p)
        self.assertEqual(len(p["hand"]), 1)
        self.assertEqual(len(p["deck"]), 14)

    def test_hand_overflow_burns_card(self):
        p = create_player("P1", "Mage")
        p["deck"] = ["Town Crier"] * 12
        p["hand"] = ["Castle Guard"] * 10  # full hand
        draw_card(p)
        self.assertEqual(len(p["hand"]), 10)   # still 10
        self.assertEqual(len(p["deck"]), 11)   # one burned

    def test_fatigue_increments_and_damages(self):
        p = create_player("P1", "Mage")
        p["deck"] = []  # empty deck
        self.assertEqual(p["hp"], 30)
        draw_card(p)
        self.assertEqual(p["fatigue"], 1)
        self.assertEqual(p["hp"], 29)
        draw_card(p)
        self.assertEqual(p["fatigue"], 2)
        self.assertEqual(p["hp"], 27)  # 29 - 2


class TestStartTurn(unittest.TestCase):
    def test_mana_increments(self):
        p = create_player("P1", "Mage")
        p["deck"] = ["Town Crier"] * 5
        start_turn(p)
        self.assertEqual(p["max_mana"], 1)
        self.assertEqual(p["mana"], 1)
        start_turn(p)
        self.assertEqual(p["max_mana"], 2)
        self.assertEqual(p["mana"], 2)

    def test_mana_capped_at_10(self):
        p = create_player("P1", "Mage")
        p["deck"] = ["Town Crier"] * 15
        p["max_mana"] = 10
        p["mana"] = 10
        start_turn(p)
        self.assertEqual(p["max_mana"], 10)
        self.assertEqual(p["mana"], 10)

    def test_hero_power_reset(self):
        p = create_player("P1", "Mage")
        p["deck"] = ["Town Crier"] * 5
        p["hero_power_used"] = True
        start_turn(p)
        self.assertFalse(p["hero_power_used"])

    def test_minion_can_attack_reset(self):
        p = create_player("P1", "Mage")
        p["deck"] = ["Town Crier"] * 5
        m = _make_minion("Town Crier", 1, 2)
        m["can_attack"] = False
        p["board"].append(m)
        start_turn(p)
        self.assertTrue(p["board"][0]["can_attack"])

    def test_draws_card(self):
        p = create_player("P1", "Mage")
        p["deck"] = ["Town Crier"] * 5
        start_turn(p)
        self.assertEqual(len(p["hand"]), 1)


class TestDoMulligan(unittest.TestCase):
    def setUp(self):
        GAME_LOG.clear()

    def test_keep_all(self):
        p = create_player("P1", "Mage")
        for _ in range(3):
            draw_card(p)
        original = list(p["hand"])
        do_mulligan(p, [])
        self.assertEqual(p["hand"], original)

    def test_swap_all(self):
        p = create_player("P1", "Mage")
        for _ in range(3):
            draw_card(p)
        do_mulligan(p, [0, 1, 2])
        self.assertEqual(len(p["hand"]), 3)
        # Deck shrinks by 3 (replacement draws) then grows by 3 (returned cards): net 0
        self.assertEqual(len(p["deck"]), 12)

    def test_no_redeal_of_swapped_cards(self):
        """Mulligan must never give back the same cards that were just swapped."""
        p = create_player("P1", "Mage", shuffle=False)
        # Fill the deck entirely with one type of card so replacements are
        # always that type, and put a different type in the hand to swap.
        p["deck"] = ["Storybook Dragon"] * 12
        p["hand"] = ["Town Crier"] * 3
        do_mulligan(p, [0, 1, 2])
        # All replacement draws must come from the pre-existing deck, which
        # contains only Storybook Dragon.
        self.assertEqual(p["hand"], ["Storybook Dragon"] * 3)
        # Swapped cards must be back in the deck somewhere.
        self.assertIn("Town Crier", p["deck"])

    def test_partial_swap_no_redeal(self):
        """Partial swap must not redeal the swapped card."""
        p = create_player("P1", "Mage", shuffle=False)
        p["deck"] = ["Storybook Dragon"] * 12
        p["hand"] = ["Town Crier", "Castle Guard", "Highwayman"]
        # Swap only the first card (Town Crier)
        do_mulligan(p, [0])
        # Hand still has 3 cards
        self.assertEqual(len(p["hand"]), 3)
        # The replacement draw comes from the deck (Storybook Dragon) and is
        # appended to the end of the hand; the swapped card must NOT be in hand.
        self.assertNotIn("Town Crier", p["hand"])
        self.assertIn("Storybook Dragon", p["hand"])
        # Castle Guard and Highwayman were kept
        self.assertIn("Castle Guard", p["hand"])
        self.assertIn("Highwayman", p["hand"])
        # Swapped card is back in the deck
        self.assertIn("Town Crier", p["deck"])

    def test_hand_size_preserved(self):
        p = create_player("P1", "Mage")
        for _ in range(3):
            draw_card(p)
        do_mulligan(p, [1])
        self.assertEqual(len(p["hand"]), 3)


class TestDamageHero(unittest.TestCase):
    def test_direct_damage(self):
        p = create_player("P1", "Mage")
        damage_hero(p, 5)
        self.assertEqual(p["hp"], 25)

    def test_armor_absorbs_fully(self):
        p = create_player("P1", "Warrior")
        p["armor"] = 10
        damage_hero(p, 5)
        self.assertEqual(p["armor"], 5)
        self.assertEqual(p["hp"], 30)

    def test_armor_absorbs_partially(self):
        p = create_player("P1", "Warrior")
        p["armor"] = 3
        damage_hero(p, 5)
        self.assertEqual(p["armor"], 0)
        self.assertEqual(p["hp"], 28)  # 30 - (5-3)

    def test_zero_damage_is_noop(self):
        p = create_player("P1", "Mage")
        damage_hero(p, 0)
        self.assertEqual(p["hp"], 30)

    def test_negative_damage_is_noop(self):
        p = create_player("P1", "Mage")
        damage_hero(p, -5)
        self.assertEqual(p["hp"], 30)


class TestGetValidTargets(unittest.TestCase):
    def test_no_taunt_all_targets(self):
        opp = create_player("AI", "Mage")
        opp["board"].append(_make_minion("Minion1", 2, 2))
        opp["board"].append(_make_minion("Minion2", 3, 3))
        targets = get_valid_targets(opp, is_attack=True)
        self.assertIn("hero", targets)
        self.assertIn(0, targets)
        self.assertIn(1, targets)

    def test_taunt_restricts_targets(self):
        opp = create_player("AI", "Mage")
        opp["board"].append(_make_minion("Minion1", 2, 2, taunt=False))
        opp["board"].append(_make_minion("Taunt1",  3, 3, taunt=True))
        targets = get_valid_targets(opp, is_attack=True)
        self.assertNotIn("hero", targets)
        self.assertNotIn(0, targets)  # non-taunt minion blocked
        self.assertIn(1, targets)     # taunt minion is only valid target

    def test_spell_ignores_taunt(self):
        opp = create_player("AI", "Mage")
        opp["board"].append(_make_minion("Taunt1", 3, 3, taunt=True))
        targets = get_valid_targets(opp, is_attack=False)
        self.assertIn("hero", targets)
        self.assertIn(0, targets)


class TestGetLegalMoves(unittest.TestCase):
    def setUp(self):
        GAME_LOG.clear()

    def _player_with_hand(self, hero_class, cards, mana=10):
        p = create_player("P1", hero_class, custom_deck=cards + ["Town Crier"] * (15 - len(cards)), shuffle=False)
        p["mana"] = mana
        p["max_mana"] = mana
        for _ in range(len(cards)):
            draw_card(p)
        return p

    def test_cant_play_too_expensive(self):
        p = self._player_with_hand("Mage", ["Storybook Dragon"], mana=4)  # costs 5
        opp = create_player("AI", "Warrior")
        moves = get_legal_moves(p, opp)
        play_moves = [m for m in moves if m[0] == "play"]
        self.assertEqual(play_moves, [])

    def test_can_play_minion(self):
        p = self._player_with_hand("Mage", ["Town Crier"], mana=1)
        opp = create_player("AI", "Warrior")
        moves = get_legal_moves(p, opp)
        self.assertIn(("play", 0, None), moves)

    def test_board_full_no_minion_plays(self):
        p = self._player_with_hand("Mage", ["Town Crier"], mana=10)
        p["board"] = [_make_minion(f"M{i}", 1, 1) for i in range(7)]  # full board
        opp = create_player("AI", "Warrior")
        moves = get_legal_moves(p, opp)
        play_moves = [m for m in moves if m[0] == "play"]
        self.assertEqual(play_moves, [])

    def test_damage_spell_generates_targets(self):
        p = self._player_with_hand("Mage", ["Quill Bolt"], mana=2)
        opp = create_player("AI", "Warrior")
        opp["board"].append(_make_minion("Opp1", 2, 3))
        moves = get_legal_moves(p, opp)
        play_moves = [m for m in moves if m[0] == "play"]
        targets = {m[2] for m in play_moves}
        self.assertIn("hero", targets)
        self.assertIn(0, targets)

    def test_buff_spell_no_targets_when_board_empty(self):
        p = self._player_with_hand("Mage", ["Fairy Blessing"], mana=2)
        opp = create_player("AI", "Warrior")
        moves = get_legal_moves(p, opp)
        play_moves = [m for m in moves if m[0] == "play"]
        self.assertEqual(play_moves, [])

    def test_buff_spell_with_friendly_minion(self):
        p = self._player_with_hand("Mage", ["Fairy Blessing"], mana=2)
        p["board"].append(_make_minion("Town Crier", 1, 2))
        opp = create_player("AI", "Warrior")
        moves = get_legal_moves(p, opp)
        self.assertIn(("play", 0, 0), moves)

    def test_hero_power_warrior(self):
        p = self._player_with_hand("Warrior", [], mana=2)
        opp = create_player("AI", "Mage")
        moves = get_legal_moves(p, opp)
        self.assertIn(("hero_power", None, None), moves)

    def test_hero_power_mage_targets(self):
        p = self._player_with_hand("Mage", [], mana=2)
        opp = create_player("AI", "Mage")
        opp["board"].append(_make_minion("Opp1", 2, 3))
        moves = get_legal_moves(p, opp)
        hp_moves = [m for m in moves if m[0] == "hero_power"]
        targets = {m[2] for m in hp_moves}
        self.assertIn("hero", targets)
        self.assertIn(0, targets)

    def test_minion_attack_respects_taunt(self):
        p = create_player("P1", "Mage")
        p["mana"] = 10
        p["max_mana"] = 10
        attacker = _make_minion("Attacker", 3, 3, can_attack=True)
        p["board"].append(attacker)
        opp = create_player("AI", "Mage")
        opp["board"].append(_make_minion("Minion1", 2, 2, taunt=False))
        opp["board"].append(_make_minion("TauntM",  3, 3, taunt=True))
        moves = get_legal_moves(p, opp)
        attack_moves = [m for m in moves if m[0] == "attack"]
        targets = {m[2] for m in attack_moves}
        self.assertNotIn("hero", targets)
        self.assertNotIn(0, targets)  # non-taunt blocked
        self.assertIn(1, targets)     # only taunt valid


class TestExecuteMove(unittest.TestCase):
    def setUp(self):
        GAME_LOG.clear()

    def _setup_game(self, p1_class="Mage", p2_class="Warrior"):
        p1 = create_player("P1", p1_class)
        p2 = create_player("AI", p2_class)
        p1["mana"] = 10
        p1["max_mana"] = 10
        p2["mana"] = 10
        p2["max_mana"] = 10
        return p1, p2

    def test_play_minion(self):
        p1, p2 = self._setup_game()
        p1["hand"] = ["Town Crier"]
        execute_move(p1, p2, ("play", 0, None))
        self.assertEqual(len(p1["hand"]), 0)
        self.assertEqual(len(p1["board"]), 1)
        self.assertEqual(p1["board"][0]["name"], "Town Crier")
        self.assertEqual(p1["mana"], 9)  # cost 1

    def test_play_charge_minion_can_attack(self):
        p1, p2 = self._setup_game()
        p1["hand"] = ["Errant Knight"]
        execute_move(p1, p2, ("play", 0, None))
        self.assertTrue(p1["board"][0]["can_attack"])

    def test_play_normal_minion_cannot_attack_immediately(self):
        p1, p2 = self._setup_game()
        p1["hand"] = ["Town Crier"]
        execute_move(p1, p2, ("play", 0, None))
        self.assertFalse(p1["board"][0]["can_attack"])

    def test_play_weapon(self):
        p1, p2 = self._setup_game()
        p1["hand"] = ["Heroic Blade"]
        execute_move(p1, p2, ("play", 0, None))
        self.assertIsNotNone(p1["weapon"])
        self.assertEqual(p1["weapon"]["name"], "Heroic Blade")
        self.assertEqual(p1["weapon"]["atk"], 3)
        self.assertEqual(p1["weapon"]["durability"], 2)
        self.assertTrue(p1["hero_can_attack"])

    def test_play_damage_spell_hero(self):
        p1, p2 = self._setup_game()
        p1["hand"] = ["Quill Bolt"]  # deal 3 dmg
        execute_move(p1, p2, ("play", 0, "hero"))
        self.assertEqual(p2["hp"], 27)

    def test_play_damage_spell_minion(self):
        p1, p2 = self._setup_game()
        p1["hand"] = ["Quill Bolt"]  # deal 3 dmg
        p2["board"].append(_make_minion("Opp1", 2, 5))
        execute_move(p1, p2, ("play", 0, 0))
        self.assertEqual(p2["board"][0]["hp"], 2)

    def test_play_damage_spell_kills_minion(self):
        p1, p2 = self._setup_game()
        p1["hand"] = ["Quill Bolt"]
        p2["board"].append(_make_minion("Opp1", 2, 3))  # exactly 3 hp
        execute_move(p1, p2, ("play", 0, 0))
        self.assertEqual(len(p2["board"]), 0)  # cleaned up

    def test_play_heal_spell(self):
        p1, p2 = self._setup_game()
        p1["hp"] = 20
        p1["hand"] = ["Restorative Hymn"]  # heal 5
        execute_move(p1, p2, ("play", 0, None))
        self.assertEqual(p1["hp"], 25)

    def test_play_heal_spell_capped_at_30(self):
        p1, p2 = self._setup_game()
        p1["hp"] = 28
        p1["hand"] = ["Restorative Hymn"]  # heal 5
        execute_move(p1, p2, ("play", 0, None))
        self.assertEqual(p1["hp"], 30)  # capped at 30

    def test_play_draw_spell(self):
        p1, p2 = self._setup_game()
        p1["hand"] = ["Deductive Clue"]  # draw 2
        p1["deck"] = ["Town Crier", "Castle Guard", "Highwayman"]
        execute_move(p1, p2, ("play", 0, None))
        self.assertEqual(len(p1["hand"]), 2)

    def test_play_buff_spell(self):
        p1, p2 = self._setup_game()
        p1["board"].append(_make_minion("Town Crier", 1, 2))
        p1["hand"] = ["Fairy Blessing"]  # +2/+2
        execute_move(p1, p2, ("play", 0, 0))
        m = p1["board"][0]
        self.assertEqual(m["atk"], 3)
        self.assertEqual(m["hp"], 4)
        self.assertEqual(m["max_hp"], 4)  # max_hp also updated

    def test_play_buff_all_spell(self):
        p1, p2 = self._setup_game()
        p1["board"].append(_make_minion("M1", 1, 2))
        p1["board"].append(_make_minion("M2", 2, 3))
        p1["hand"] = ["Rallying Banner"]  # +1/+1 all
        execute_move(p1, p2, ("play", 0, None))
        self.assertEqual(p1["board"][0]["atk"], 2)
        self.assertEqual(p1["board"][0]["hp"], 3)
        self.assertEqual(p1["board"][0]["max_hp"], 3)
        self.assertEqual(p1["board"][1]["atk"], 3)
        self.assertEqual(p1["board"][1]["hp"], 4)

    def test_play_add_shield_spell(self):
        p1, p2 = self._setup_game()
        p1["board"].append(_make_minion("Town Crier", 1, 2))
        p1["hand"] = ["Enchanted Shield"]
        execute_move(p1, p2, ("play", 0, 0))
        self.assertTrue(p1["board"][0]["divine_shield"])

    def test_play_aoe_spell(self):
        p1, p2 = self._setup_game()
        p2["board"].append(_make_minion("Opp1", 2, 3))
        p2["board"].append(_make_minion("Opp2", 1, 1))
        p1["hand"] = ["Rebel's Ambush"]  # deal 2 to all enemies
        execute_move(p1, p2, ("play", 0, None))
        self.assertEqual(p2["board"][0]["hp"], 1)  # 3 - 2
        self.assertEqual(len(p2["board"]), 1)      # Opp2 (1hp) died

    def test_play_heal_all_spell(self):
        p1, p2 = self._setup_game()
        p1["hp"] = 25
        m1 = _make_minion("M1", 2, 3)
        m1["max_hp"] = 5
        m1["hp"] = 2
        p1["board"].append(m1)
        p1["hand"] = ["Circle of Mending"]  # heal all 3
        execute_move(p1, p2, ("play", 0, None))
        self.assertEqual(p1["hp"], 28)           # 25 + 3
        self.assertEqual(p1["board"][0]["hp"], 5)  # 2 + 3 = 5 (capped at max_hp)

    def test_attack_minion(self):
        p1, p2 = self._setup_game()
        attacker = _make_minion("Attacker", 3, 4, can_attack=True)
        p1["board"].append(attacker)
        defender = _make_minion("Defender", 2, 5)
        p2["board"].append(defender)
        execute_move(p1, p2, ("attack", 0, 0))
        self.assertEqual(p1["board"][0]["hp"], 2)  # 4 - 2 retaliation
        self.assertEqual(p2["board"][0]["hp"], 2)  # 5 - 3

    def test_attack_hero(self):
        p1, p2 = self._setup_game()
        attacker = _make_minion("Attacker", 4, 4, can_attack=True)
        p1["board"].append(attacker)
        execute_move(p1, p2, ("attack", 0, "hero"))
        self.assertEqual(p2["hp"], 26)
        self.assertFalse(p1["board"][0]["can_attack"])

    def test_attack_exhausts_attacker(self):
        p1, p2 = self._setup_game()
        attacker = _make_minion("Attacker", 2, 3, can_attack=True)
        p1["board"].append(attacker)
        execute_move(p1, p2, ("attack", 0, "hero"))
        self.assertFalse(p1["board"][0]["can_attack"])

    def test_divine_shield_blocks_attack(self):
        p1, p2 = self._setup_game()
        attacker = _make_minion("Attacker", 3, 4, can_attack=True)
        p1["board"].append(attacker)
        shielded = _make_minion("Shielded", 2, 5, divine_shield=True)
        p2["board"].append(shielded)
        execute_move(p1, p2, ("attack", 0, 0))
        self.assertFalse(p2["board"][0].get("divine_shield"))  # shield consumed
        self.assertEqual(p2["board"][0]["hp"], 5)   # no damage
        self.assertEqual(p1["board"][0]["hp"], 2)   # attacker still takes retaliation

    def test_poisonous_kills_defender(self):
        p1, p2 = self._setup_game()
        poison = _make_minion("PoisonMinion", 1, 4, can_attack=True, poisonous=True)
        p1["board"].append(poison)
        big = _make_minion("BigMinion", 2, 100)
        p2["board"].append(big)
        execute_move(p1, p2, ("attack", 0, 0))
        self.assertEqual(len(p2["board"]), 0)  # poisonous killed it

    def test_hero_power_warrior_armor(self):
        p1, p2 = self._setup_game("Warrior")
        p1["mana"] = 2
        execute_move(p1, p2, ("hero_power", None, None))
        self.assertEqual(p1["armor"], 2)
        self.assertTrue(p1["hero_power_used"])
        self.assertEqual(p1["mana"], 0)

    def test_hero_power_mage_damage(self):
        p1, p2 = self._setup_game("Mage")
        p1["mana"] = 2
        execute_move(p1, p2, ("hero_power", None, "hero"))
        self.assertEqual(p2["hp"], 29)
        self.assertTrue(p1["hero_power_used"])

    def test_hero_power_priest_heal(self):
        p1, p2 = self._setup_game("Priest")
        p1["hp"] = 25
        p1["mana"] = 2
        execute_move(p1, p2, ("hero_power", None, "hero"))
        self.assertEqual(p1["hp"], 27)

    def test_hero_power_rogue_dagger(self):
        p1, p2 = self._setup_game("Rogue")
        p1["mana"] = 2
        execute_move(p1, p2, ("hero_power", None, None))
        self.assertIsNotNone(p1["weapon"])
        self.assertEqual(p1["weapon"]["name"], "Wicked Dagger")
        self.assertTrue(p1["hero_can_attack"])

    def test_hero_attack_with_weapon(self):
        p1, p2 = self._setup_game()
        p1["weapon"] = {"name": "Heroic Blade", "atk": 3, "durability": 2}
        p1["hero_can_attack"] = True
        execute_move(p1, p2, ("hero_attack", None, "hero"))
        self.assertEqual(p2["hp"], 27)
        self.assertEqual(p1["weapon"]["durability"], 1)

    def test_hero_attack_weapon_breaks(self):
        p1, p2 = self._setup_game()
        p1["weapon"] = {"name": "Wicked Dagger", "atk": 1, "durability": 1}
        p1["hero_can_attack"] = True
        execute_move(p1, p2, ("hero_attack", None, "hero"))
        self.assertIsNone(p1["weapon"])

    def test_battlecry_heal(self):
        p1, p2 = self._setup_game()
        p1["hp"] = 25
        p1["hand"] = ["Cathedral Cleric"]  # battlecry: heal hero 3
        execute_move(p1, p2, ("play", 0, None))
        self.assertEqual(p1["hp"], 28)

    def test_battlecry_draw(self):
        p1, p2 = self._setup_game()
        p1["hand"] = ["Sherlock Holmes"]  # battlecry: draw 2
        p1["deck"] = ["Town Crier", "Castle Guard", "Highwayman"]
        execute_move(p1, p2, ("play", 0, None))
        self.assertEqual(len(p1["hand"]), 2)

    def test_deathrattle_fires(self):
        p1, p2 = self._setup_game()
        m = _make_minion("Tinker Alchemist", 1, 1)
        m["deathrattle"] = {"effect": "dmg_hero", "val": 2}
        m["hp"] = 1
        p2["board"].append(_make_minion("Opp1", 2, 1, can_attack=True))
        p1["board"].append(m)
        # AI minion attacks Tinker Alchemist — should trigger deathrattle
        execute_move(p2, p1, ("attack", 0, 0))
        # Tinker Alchemist should be dead and deathrattle should have fired
        self.assertEqual(len(p1["board"]), 0)
        self.assertEqual(p2["hp"], 28)  # deathrattle dealt 2 to opponent (p2 is the enemy)


class TestCheckWin(unittest.TestCase):
    def test_no_winner(self):
        p1 = create_player("P1", "Mage")
        p2 = create_player("AI", "Warrior")
        self.assertIsNone(check_win(p1, p2))

    def test_p1_wins(self):
        p1 = create_player("P1", "Mage")
        p2 = create_player("AI", "Warrior")
        p2["hp"] = 0
        self.assertEqual(check_win(p1, p2), "P1")

    def test_p2_wins(self):
        p1 = create_player("P1", "Mage")
        p2 = create_player("AI", "Warrior")
        p1["hp"] = 0
        self.assertEqual(check_win(p1, p2), "AI")

    def test_draw(self):
        p1 = create_player("P1", "Mage")
        p2 = create_player("AI", "Warrior")
        p1["hp"] = 0
        p2["hp"] = 0
        self.assertEqual(check_win(p1, p2), "DRAW")

    def test_negative_hp(self):
        p1 = create_player("P1", "Mage")
        p2 = create_player("AI", "Warrior")
        p1["hp"] = -5
        self.assertEqual(check_win(p1, p2), "AI")


class TestCleanupDead(unittest.TestCase):
    def setUp(self):
        GAME_LOG.clear()

    def test_dead_minion_removed(self):
        p1 = create_player("P1", "Mage")
        p2 = create_player("AI", "Warrior")
        dead = _make_minion("Dead", 1, 0)  # 0 hp = dead
        alive = _make_minion("Alive", 2, 3)
        p1["board"] = [dead, alive]
        cleanup_dead(p1, p2)
        self.assertEqual(len(p1["board"]), 1)
        self.assertEqual(p1["board"][0]["name"], "Alive")

    def test_deathrattle_triggered(self):
        p1 = create_player("P1", "Mage")
        p2 = create_player("AI", "Warrior")
        dead = _make_minion("DRMinion", 1, 0)
        dead["deathrattle"] = {"effect": "dmg_hero", "val": 3}
        p1["board"] = [dead]
        cleanup_dead(p1, p2)
        self.assertEqual(p2["hp"], 27)  # took 3 deathrattle damage


class TestRunAiTurn(unittest.TestCase):
    def setUp(self):
        GAME_LOG.clear()

    def test_ai_starts_turn(self):
        p1 = create_player("P1", "Mage")
        for _ in range(3):
            draw_card(p1)
        p2 = create_player("AI", "Warrior")
        p2["deck"] = ["Town Crier"] * 15
        for _ in range(4):
            draw_card(p2)
        moves = run_ai_turn(p2, p1)
        # AI should have mana and may play cards
        self.assertIsInstance(moves, list)

    def test_ai_does_not_crash_empty_hand(self):
        p1 = create_player("P1", "Mage")
        p2 = create_player("AI", "Warrior")
        p2["deck"] = []
        p2["hand"] = []
        moves = run_ai_turn(p2, p1)
        self.assertEqual(moves, [])

    def test_ai_plays_charge_minion(self):
        """AI with a cheap charge minion should play and attack with it."""
        p1 = create_player("P1", "Mage")
        p1["hp"] = 30
        p2 = create_player("AI", "Warrior")
        p2["hand"] = ["Errant Knight"]  # 3 mana, charge
        p2["deck"] = ["Town Crier"] * 14
        p2["mana"] = 10
        p2["max_mana"] = 10
        # run_ai_turn calls start_turn internally which resets mana to max_mana
        # So we need max_mana set before run_ai_turn
        moves = run_ai_turn(p2, p1)
        # Should have at least played the Errant Knight and possibly attacked
        played = [m for m in moves if m[0] == "play"]
        self.assertTrue(len(played) >= 1)

    def test_ai_stops_when_game_over(self):
        """AI should not make more moves if game is already won."""
        p1 = create_player("P1", "Mage")
        p1["hp"] = 1
        p2 = create_player("AI", "Warrior")
        big = _make_minion("Big", 10, 10, can_attack=True)
        p2["board"].append(big)
        p2["hand"] = []
        p2["deck"] = ["Town Crier"] * 15
        # Give AI enough mana
        p2["max_mana"] = 10
        # Manually call start_turn and execute one attack to simulate
        start_turn(p2)
        # After the first attack that kills P1, AI should stop
        moves = run_ai_turn(p2, p1)
        self.assertIsNotNone(check_win(p1, p2))  # game should be over


class TestEvaluateAiMove(unittest.TestCase):
    """Tests for evaluate_ai_move scoring."""

    def setUp(self):
        GAME_LOG.clear()

    def _setup_ai_game(self):
        p1 = create_player("P1", "Mage")
        p2 = create_player("AI", "Mage")
        p1["mana"] = 10
        p1["max_mana"] = 10
        p2["mana"] = 10
        p2["max_mana"] = 10
        return p1, p2

    def test_heal_spell_scores_positively_when_hurt(self):
        """AI should value a heal spell when it is damaged."""
        p1, p2 = self._setup_ai_game()
        p2["hp"] = 10  # badly hurt
        p2["hand"] = ["Restorative Hymn"]  # heal 5
        move = ("play", 0, None)
        score = evaluate_ai_move(p2, p1, move)
        self.assertGreater(score, 0)

    def test_heal_spell_low_score_when_full_hp(self):
        """AI should score a heal spell lower at full HP than when damaged."""
        p1, p2_full = self._setup_ai_game()
        _, p2_hurt = self._setup_ai_game()
        p2_full["hp"] = 30  # full HP — effective heal is 0
        p2_full["hand"] = ["Restorative Hymn"]
        p2_hurt["hp"] = 15  # badly hurt — effective heal is 5
        p2_hurt["hand"] = ["Restorative Hymn"]
        score_full = evaluate_ai_move(p2_full, p1, ("play", 0, None))
        score_hurt = evaluate_ai_move(p2_hurt, p1, ("play", 0, None))
        self.assertLess(score_full, score_hurt)

    def test_heal_spell_score_increases_with_damage(self):
        """More damage taken → higher heal-spell score."""
        p1, p2_healthy = self._setup_ai_game()
        _, p2_hurt = self._setup_ai_game()
        p2_healthy["hp"] = 28
        p2_healthy["hand"] = ["Elixir of Life"]
        p2_hurt["hp"] = 10
        p2_hurt["hand"] = ["Elixir of Life"]
        score_healthy = evaluate_ai_move(p2_healthy, p1, ("play", 0, None))
        score_hurt = evaluate_ai_move(p2_hurt, p1, ("play", 0, None))
        self.assertGreater(score_hurt, score_healthy)

    def test_lethal_attack_gets_high_score(self):
        """An attack that kills the opponent hero should score very highly."""
        p1, p2 = self._setup_ai_game()
        p1["hp"] = 3
        attacker = _make_minion("Big", 5, 5, can_attack=True)
        p2["board"].append(attacker)
        move = ("attack", 0, "hero")
        score = evaluate_ai_move(p2, p1, move)
        self.assertGreaterEqual(score, 1000)


class TestExecuteMoveCleanup(unittest.TestCase):
    """Tests for cleanup_dead being called even in error paths."""

    def setUp(self):
        GAME_LOG.clear()

    def _setup_game(self):
        p1 = create_player("P1", "Mage")
        p2 = create_player("AI", "Warrior")
        p1["mana"] = 10
        p1["max_mana"] = 10
        return p1, p2

    def test_dead_minion_cleaned_up_after_buff_invalid_target(self):
        """cleanup_dead must run even if a buff card has an out-of-range target."""
        p1, p2 = self._setup_game()
        # Place a dead minion on p1's board manually (should be cleaned up)
        dead = _make_minion("DeadOne", 1, 0)
        p1["board"] = [dead]
        p1["hand"]  = ["Fairy Blessing"]  # buff +2/+2
        # Target index 5 is clearly out of range (board has 1 minion at index 0)
        execute_move(p1, p2, ("play", 0, 5))
        # The dead minion should have been cleaned up
        self.assertEqual(len(p1["board"]), 0)

    def test_dead_minion_cleaned_up_after_add_shield_invalid_target(self):
        """cleanup_dead must run even if an add_shield card has an out-of-range target."""
        p1, p2 = self._setup_game()
        dead = _make_minion("DeadOne", 1, 0)
        p1["board"] = [dead]
        p1["hand"]  = ["Enchanted Shield"]
        execute_move(p1, p2, ("play", 0, 5))
        self.assertEqual(len(p1["board"]), 0)


class TestCardDbIntegrity(unittest.TestCase):
    """Verify CARD_DB entries have required fields."""

    def test_all_minions_have_required_fields(self):
        for name, card in CARD_DB.items():
            with self.subTest(card=name):
                self.assertIn("type", card)
                self.assertIn("cost", card)
                self.assertIn("icon", card)
                if card["type"] == "minion":
                    self.assertIn("atk", card)
                    self.assertIn("hp", card)
                elif card["type"] == "spell":
                    self.assertIn("effect", card)
                elif card["type"] == "weapon":
                    self.assertIn("atk", card)
                    self.assertIn("durability", card)

    def test_legendary_max_copies(self):
        """Legendary cards should have max 1 copy in auto-generated decks."""
        p = create_player("P", "Mage")
        for name in p["deck"]:
            if CARD_DB[name].get("legendary"):
                count = p["deck"].count(name)
                self.assertLessEqual(
                    count, 1,
                    f"Legendary '{name}' should appear at most once but appears {count} times in deck"
                )

    def test_non_legendary_max_copies(self):
        """Non-legendary cards should have at most 2 copies."""
        p = create_player("P", "Mage")
        for name in set(p["deck"]):
            if not CARD_DB[name].get("legendary"):
                count = p["deck"].count(name)
                self.assertLessEqual(count, 2, f"'{name}' appears {count} times")

    def test_hero_classes_valid(self):
        self.assertEqual(HERO_CLASSES, ["Mage", "Warrior", "Priest", "Rogue"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
