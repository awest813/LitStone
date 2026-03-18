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
        # Verify the corrected cost (was 3, now 2)
        from game_logic import CARD_DB
        self.assertEqual(CARD_DB["Heroic Blade"]["cost"], 2)

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

    def test_attacker_divine_shield_not_consumed_by_zero_attack_defender(self):
        """Divine shield must NOT be consumed when the defender has 0 attack (no retaliation)."""
        p1, p2 = self._setup_game()
        attacker = _make_minion("Attacker", 3, 4, can_attack=True, divine_shield=True)
        p1["board"].append(attacker)
        zero_atk_defender = _make_minion("Dummy", 0, 5)
        p2["board"].append(zero_atk_defender)
        execute_move(p1, p2, ("attack", 0, 0))
        # Attacker's divine shield should still be intact — there was nothing to block
        self.assertTrue(p1["board"][0].get("divine_shield"),
                        "divine_shield was wrongly consumed by a 0-attack defender")
        # Defender took damage normally
        self.assertEqual(p2["board"][0]["hp"], 2)

    def test_attacker_divine_shield_consumed_by_nonzero_attack_defender(self):
        """Divine shield IS consumed when defender has non-zero attack."""
        p1, p2 = self._setup_game()
        attacker = _make_minion("Attacker", 3, 4, can_attack=True, divine_shield=True)
        p1["board"].append(attacker)
        defender = _make_minion("Defender", 2, 5)
        p2["board"].append(defender)
        execute_move(p1, p2, ("attack", 0, 0))
        self.assertFalse(p1["board"][0].get("divine_shield"))  # consumed
        self.assertEqual(p1["board"][0]["hp"], 4)   # no damage taken

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

    def test_enchanted_shield_costs_one_mana(self):
        """Enchanted Shield should cost 1 mana after balance fix."""
        p1, p2 = self._setup_game()
        p1["mana"] = 1
        p1["max_mana"] = 1
        p1["board"].append(_make_minion("Town Crier", 1, 2))
        p1["hand"] = ["Enchanted Shield"]
        execute_move(p1, p2, ("play", 0, 0))
        self.assertTrue(p1["board"][0]["divine_shield"])
        self.assertEqual(p1["mana"], 0)

    def test_inkwell_blast_deals_one_to_all_enemy_minions(self):
        """Inkwell Blast (2 mana) deals 1 damage to every enemy minion."""
        p1, p2 = self._setup_game()
        p2["board"].append(_make_minion("Opp1", 1, 3))
        p2["board"].append(_make_minion("Opp2", 2, 1))  # will die
        p1["hand"] = ["Inkwell Blast"]
        execute_move(p1, p2, ("play", 0, None))
        self.assertEqual(p2["board"][0]["hp"], 2)   # 3 - 1
        self.assertEqual(len(p2["board"]), 1)        # Opp2 (1 hp) destroyed
        self.assertEqual(p1["mana"], 8)              # 10 - 2

    def test_merlin_battlecry_heals_hero(self):
        """Merlin's battlecry should heal the hero for 6 HP (not draw cards)."""
        p1, p2 = self._setup_game()
        p1["hp"] = 20
        p1["hand"] = ["Merlin"]
        execute_move(p1, p2, ("play", 0, None))
        self.assertEqual(p1["hp"], 26)  # 20 + 6 from Merlin's battlecry

    def test_big_bad_wolf_is_poisonous_and_charge(self):
        """The Big Bad Wolf should be both poisonous and charge after differentiation."""
        from game_logic import CARD_DB
        bbw = CARD_DB["The Big Bad Wolf"]
        self.assertTrue(bbw.get("poisonous"), "Big Bad Wolf should be poisonous")
        self.assertTrue(bbw.get("charge"), "Big Bad Wolf should have charge")

    def test_little_red_riding_hood_different_stats_from_robin_hood(self):
        """LRRH and Robin Hood should have different stat distributions."""
        from game_logic import CARD_DB
        lrrh = CARD_DB["Little Red Riding Hood"]
        rh = CARD_DB["Robin Hood"]
        self.assertNotEqual(
            (lrrh["atk"], lrrh["hp"]), (rh["atk"], rh["hp"]),
            "Little Red Riding Hood and Robin Hood should have different atk/hp"
        )

    def test_morgan_le_fay_has_divine_shield_not_poisonous(self):
        """Morgan le Fay should be differentiated from Baba Yaga by using divine_shield."""
        from game_logic import CARD_DB
        mlf = CARD_DB["Morgan le Fay"]
        self.assertFalse(mlf.get("poisonous"), "Morgan le Fay should no longer be poisonous")
        self.assertTrue(mlf.get("divine_shield"), "Morgan le Fay should have divine_shield")


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


class TestSilenceMechanic(unittest.TestCase):
    """Tests for the Tome of Silence spell."""

    def setUp(self):
        GAME_LOG.clear()

    def _setup_game(self):
        p1 = create_player("P1", "Mage")
        p2 = create_player("AI", "Warrior")
        p1["mana"] = 10
        p1["max_mana"] = 10
        p2["mana"] = 10
        p2["max_mana"] = 10
        return p1, p2

    def test_silence_removes_taunt(self):
        p1, p2 = self._setup_game()
        taunter = _make_minion("Castle Guard", 2, 3, taunt=True)
        p2["board"].append(taunter)
        p1["hand"] = ["Tome of Silence"]
        execute_move(p1, p2, ("play", 0, 0))
        self.assertFalse(p2["board"][0].get("taunt"), "Taunt should be removed after silence")

    def test_silence_removes_divine_shield(self):
        p1, p2 = self._setup_game()
        shielded = _make_minion("Templar", 3, 3, divine_shield=True)
        p2["board"].append(shielded)
        p1["hand"] = ["Tome of Silence"]
        execute_move(p1, p2, ("play", 0, 0))
        self.assertFalse(p2["board"][0].get("divine_shield"))

    def test_silence_removes_poisonous(self):
        p1, p2 = self._setup_game()
        poisoner = _make_minion("Cave Spider", 1, 2, poisonous=True)
        p2["board"].append(poisoner)
        p1["hand"] = ["Tome of Silence"]
        execute_move(p1, p2, ("play", 0, 0))
        self.assertFalse(p2["board"][0].get("poisonous"))

    def test_silence_removes_deathrattle(self):
        p1, p2 = self._setup_game()
        dr_minion = _make_minion("DRMinion", 1, 3)
        dr_minion["deathrattle"] = {"effect": "dmg_hero", "val": 3}
        p2["board"].append(dr_minion)
        p1["hand"] = ["Tome of Silence"]
        execute_move(p1, p2, ("play", 0, 0))
        self.assertNotIn("deathrattle", p2["board"][0], "Deathrattle should be removed after silence")

    def test_silence_preserves_stats(self):
        p1, p2 = self._setup_game()
        minion = _make_minion("Minion", 4, 5, taunt=True, divine_shield=True)
        p2["board"].append(minion)
        p1["hand"] = ["Tome of Silence"]
        execute_move(p1, p2, ("play", 0, 0))
        self.assertEqual(p2["board"][0]["atk"], 4)
        self.assertEqual(p2["board"][0]["hp"], 5)

    def test_silence_targets_only_enemy_minions_in_legal_moves(self):
        p1 = create_player("P1", "Mage")
        p2 = create_player("AI", "Warrior")
        p1["mana"] = 10
        p1["max_mana"] = 10
        p2["board"].append(_make_minion("EnemyM", 2, 3))
        p1["board"].append(_make_minion("FriendlyM", 1, 2))
        p1["hand"] = ["Tome of Silence"]
        moves = get_legal_moves(p1, p2)
        play_moves = [m for m in moves if m[0] == "play"]
        # Only enemy board index 0 should be valid target, not hero, not friendly
        self.assertIn(("play", 0, 0), play_moves)  # target enemy minion at index 0
        self.assertNotIn(("play", 0, "hero"), play_moves)
        self.assertNotIn(("play", 0, None), play_moves)

    def test_silence_no_legal_moves_when_enemy_board_empty(self):
        p1 = create_player("P1", "Mage")
        p2 = create_player("AI", "Warrior")
        p1["mana"] = 10
        p1["max_mana"] = 10
        p1["hand"] = ["Tome of Silence"]
        moves = get_legal_moves(p1, p2)
        play_moves = [m for m in moves if m[0] == "play"]
        self.assertEqual(play_moves, [])

    def test_silence_silenced_deathrattle_does_not_fire(self):
        """After silence, deathrattle must not fire when the minion dies."""
        p1, p2 = self._setup_game()
        p2["hp"] = 30
        dr_minion = _make_minion("DRMinion", 1, 1)
        dr_minion["deathrattle"] = {"effect": "dmg_hero", "val": 5}
        p2["board"].append(dr_minion)
        # Silence the deathrattle minion
        p1["hand"] = ["Tome of Silence"]
        execute_move(p1, p2, ("play", 0, 0))
        # Now kill it with a damage spell
        p1["hand"] = ["Quill Bolt"]  # 3 damage — enough to kill hp=1
        p1["mana"] = 10
        execute_move(p1, p2, ("play", 0, 0))
        # Deathrattle should NOT have fired
        self.assertEqual(p2["hp"], 30, "Silenced deathrattle must not deal damage")


class TestHeroAttackEdgeCases(unittest.TestCase):
    """Additional tests for hero_attack interactions."""

    def setUp(self):
        GAME_LOG.clear()

    def _setup_game(self):
        p1 = create_player("P1", "Mage")
        p2 = create_player("AI", "Warrior")
        p1["mana"] = 10
        p1["max_mana"] = 10
        return p1, p2

    def test_hero_attack_zero_atk_defender_no_retaliation_damage(self):
        """Hero attacks a 0-atk minion → hero takes no damage."""
        p1, p2 = self._setup_game()
        p1["weapon"] = {"name": "Heroic Blade", "atk": 3, "durability": 2}
        p1["hero_can_attack"] = True
        p2["board"].append(_make_minion("Dummy", 0, 5))
        execute_move(p1, p2, ("hero_attack", None, 0))
        self.assertEqual(p1["hp"], 30, "Hero should take 0 damage when attacking a 0-atk minion")

    def test_hero_attack_divine_shield_weapon_durability_consumed(self):
        """Hero attacks a divine-shielded minion: shield pops, weapon durability still consumed."""
        p1, p2 = self._setup_game()
        p1["weapon"] = {"name": "Heroic Blade", "atk": 3, "durability": 2}
        p1["hero_can_attack"] = True
        p2["board"].append(_make_minion("Shielded", 2, 5, divine_shield=True))
        execute_move(p1, p2, ("hero_attack", None, 0))
        self.assertFalse(p2["board"][0].get("divine_shield"))  # shield popped
        self.assertEqual(p2["board"][0]["hp"], 5)               # no damage
        self.assertEqual(p1["weapon"]["durability"], 1)          # durability consumed

    def test_hero_attack_with_retaliation_damages_hero(self):
        """Hero attacking a minion with non-zero attack does take retaliation damage."""
        p1, p2 = self._setup_game()
        p1["weapon"] = {"name": "Heroic Blade", "atk": 3, "durability": 2}
        p1["hero_can_attack"] = True
        p2["board"].append(_make_minion("Attacker", 4, 5))
        execute_move(p1, p2, ("hero_attack", None, 0))
        self.assertEqual(p1["hp"], 26, "Hero should take 4 retaliation damage")


class TestPaladinHeroPower(unittest.TestCase):
    """Tests for the Paladin Reinforce hero power."""

    def setUp(self):
        GAME_LOG.clear()

    def test_paladin_hero_power_summons_recruit(self):
        p1 = create_player("P1", "Paladin")
        p2 = create_player("AI", "Mage")
        p1["mana"] = 2
        p1["max_mana"] = 2
        execute_move(p1, p2, ("hero_power", None, None))
        self.assertEqual(len(p1["board"]), 1)
        self.assertEqual(p1["board"][0]["name"], "Silver Hand Recruit")
        self.assertEqual(p1["board"][0]["atk"], 1)
        self.assertEqual(p1["board"][0]["hp"], 1)

    def test_paladin_hero_power_costs_2_mana(self):
        p1 = create_player("P1", "Paladin")
        p2 = create_player("AI", "Mage")
        p1["mana"] = 2
        p1["max_mana"] = 2
        execute_move(p1, p2, ("hero_power", None, None))
        self.assertEqual(p1["mana"], 0)
        self.assertTrue(p1["hero_power_used"])

    def test_paladin_hero_power_not_available_when_board_full(self):
        p1 = create_player("P1", "Paladin")
        p2 = create_player("AI", "Mage")
        p1["mana"] = 2
        p1["max_mana"] = 2
        p1["board"] = [_make_minion(f"M{i}", 1, 1) for i in range(7)]
        moves = get_legal_moves(p1, p2)
        hp_moves = [m for m in moves if m[0] == "hero_power"]
        self.assertEqual(hp_moves, [], "Paladin hero power must not be available when board is full")

    def test_paladin_in_hero_classes(self):
        self.assertIn("Paladin", HERO_CLASSES)

    def test_paladin_create_player(self):
        p = create_player("P", "Paladin")
        self.assertEqual(p["hero_class"], "Paladin")


class TestNewCards(unittest.TestCase):
    """Tests for newly added cards: Ivanhoe, Quasimodo, Don Quixote, Tome of Silence."""

    def setUp(self):
        GAME_LOG.clear()

    def test_ivanhoe_has_taunt_and_divine_shield(self):
        card = CARD_DB["Ivanhoe"]
        self.assertTrue(card.get("taunt"))
        self.assertTrue(card.get("divine_shield"))
        self.assertTrue(card.get("legendary"))

    def test_quasimodo_has_taunt_and_battlecry(self):
        card = CARD_DB["Quasimodo"]
        self.assertTrue(card.get("taunt"))
        self.assertIn("battlecry", card)
        self.assertEqual(card["battlecry"]["effect"], "heal_hero")

    def test_quasimodo_battlecry_heals_hero(self):
        p1 = create_player("P1", "Mage")
        p2 = create_player("AI", "Warrior")
        p1["mana"] = 10
        p1["max_mana"] = 10
        p1["hp"] = 25
        p1["hand"] = ["Quasimodo"]
        execute_move(p1, p2, ("play", 0, None))
        self.assertEqual(p1["hp"], 27)  # +2 from battlecry

    def test_don_quixote_has_charge(self):
        card = CARD_DB["Don Quixote"]
        self.assertTrue(card.get("charge"))
        self.assertTrue(card.get("legendary"))

    def test_tome_of_silence_in_card_db(self):
        card = CARD_DB["Tome of Silence"]
        self.assertEqual(card["type"], "spell")
        self.assertEqual(card["effect"], "silence")
        self.assertEqual(card["cost"], 3)

    def test_new_cards_have_required_fields(self):
        for name in ("Ivanhoe", "Quasimodo", "Don Quixote", "Tome of Silence"):
            with self.subTest(card=name):
                card = CARD_DB[name]
                self.assertIn("type", card)
                self.assertIn("cost", card)
                self.assertIn("icon", card)


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
        self.assertEqual(HERO_CLASSES, ["Mage", "Warrior", "Priest", "Rogue", "Paladin"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
