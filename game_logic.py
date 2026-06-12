"""
game_logic.py — Pure Python game logic for LitStone.
No Tkinter/GUI dependencies. All emoji replaced with text codes
so log entries render safely in any environment.
"""

import random

# ---------------------------------------------------------------------------
# 1. CARD DATABASE & CONFIGURATION
# ---------------------------------------------------------------------------

DECK_SIZE = 30
DEFAULT_HERO_HP = 30
MAX_MANA = 10
MAX_BOARD_SIZE = 7
MAX_HAND_SIZE = 10
OPENING_HAND_FIRST = 3
OPENING_HAND_SECOND = 4
COIN_CARD = "The Coin"
MINION_TRAITS = ("taunt", "divine_shield", "charge", "poisonous", "battlecry", "deathrattle")

CARD_DB = {
    # ---------- Standard cards ----------
    "Town Crier":       {"type": "minion", "cost": 1, "atk": 1, "hp": 2, "taunt": False, "icon": "TC"},
    "Castle Guard":     {"type": "minion", "cost": 2, "atk": 2, "hp": 3, "taunt": True,  "icon": "CG"},
    "Highwayman":       {"type": "minion", "cost": 3, "atk": 3, "hp": 3, "taunt": False, "icon": "HW"},
    "Errant Knight":    {"type": "minion", "cost": 3, "atk": 3, "hp": 2, "charge": True, "icon": "EK"},
    "Templar Captain":  {"type": "minion", "cost": 4, "atk": 3, "hp": 3, "taunt": True,  "divine_shield": True, "icon": "TP"},
    "Storybook Dragon": {"type": "minion", "cost": 5, "atk": 5, "hp": 6, "taunt": False, "icon": "SD"},
    "Cave Spider":      {"type": "minion", "cost": 2, "atk": 1, "hp": 2, "poisonous": True, "icon": "CS"},
    "Cathedral Cleric": {"type": "minion", "cost": 2, "atk": 2, "hp": 2, "battlecry": {"effect": "heal_hero", "val": 3}, "icon": "CC"},
    "Tinker Alchemist": {"type": "minion", "cost": 2, "atk": 1, "hp": 1, "deathrattle": {"effect": "dmg_hero", "val": 2}, "icon": "TA"},

    # ---------- Spells & weapon ----------
    "Quill Bolt":       {"type": "spell",  "cost": 2, "effect": "damage",     "val": 3, "icon": "QB"},
    "Inferno Verse":    {"type": "spell",  "cost": 4, "effect": "damage",     "val": 6, "icon": "IV"},
    "Restorative Hymn": {"type": "spell",  "cost": 3, "effect": "heal",       "val": 5, "icon": "HY"},
    "Deductive Clue":   {"type": "spell",  "cost": 3, "effect": "draw",       "val": 2, "icon": "DC"},
    "Rebel's Ambush":   {"type": "spell",  "cost": 4, "effect": "damage_all", "val": 2, "icon": "RA"},
    "Fairy Blessing":   {"type": "spell",  "cost": 2, "effect": "buff",       "val": [2, 2], "icon": "FB"},
    "Heroic Blade":     {"type": "weapon", "cost": 2, "atk": 3, "durability": 2, "icon": "HB"},

    # ---------- Legendary minions (max 1 copy per deck) ----------
    "Sherlock Holmes": {"type": "minion", "cost": 5, "atk": 2, "hp": 6,
                        "battlecry": {"effect": "draw_cards", "val": 2},
                        "legendary": True, "icon": "SH"},
    "Dr. John Watson": {"type": "minion", "cost": 4, "atk": 3, "hp": 5,
                        "battlecry": {"effect": "heal_hero", "val": 4},
                        "legendary": True, "icon": "JW"},
    "Professor Moriarty": {"type": "minion", "cost": 6, "atk": 5, "hp": 5, "poisonous": True,
                           "deathrattle": {"effect": "dmg_hero", "val": 3},
                           "legendary": True, "icon": "PM"},
    "Van Helsing": {"type": "minion", "cost": 5, "atk": 5, "hp": 4, "charge": True,
                    "legendary": True, "icon": "VH"},
    "Victor Frankenstein": {"type": "minion", "cost": 4, "atk": 3, "hp": 6,
                            "battlecry": {"effect": "draw_cards", "val": 1},
                            "legendary": True, "icon": "VF"},
    "Frankenstein's Monster": {"type": "minion", "cost": 6, "atk": 6, "hp": 6, "taunt": True,
                               "deathrattle": {"effect": "dmg_hero", "val": 3},
                               "legendary": True, "icon": "FM"},
    "Alice": {"type": "minion", "cost": 3, "atk": 3, "hp": 4,
              "battlecry": {"effect": "draw_cards", "val": 1},
              "legendary": True, "icon": "AL"},
    "The Mad Hatter": {"type": "minion", "cost": 6, "atk": 4, "hp": 5,
                       "battlecry": {"effect": "draw_cards", "val": 2},
                       "legendary": True, "icon": "MH"},
    "The White Rabbit": {"type": "minion", "cost": 3, "atk": 2, "hp": 3, "charge": True,
                         "legendary": True, "icon": "RB"},
    "The Queen of Hearts": {"type": "minion", "cost": 6, "atk": 6, "hp": 5, "taunt": True,
                            "legendary": True, "icon": "QH"},
    "The Cheshire Cat": {"type": "minion", "cost": 4, "atk": 4, "hp": 4, "divine_shield": True,
                         "legendary": True, "icon": "CH"},
    "Snow White": {"type": "minion", "cost": 5, "atk": 3, "hp": 7, "divine_shield": True,
                   "legendary": True, "icon": "SW"},
    "Rapunzel": {"type": "minion", "cost": 4, "atk": 2, "hp": 6,
                 "battlecry": {"effect": "heal_hero", "val": 3},
                 "legendary": True, "icon": "RP"},
    "Sleeping Beauty": {"type": "minion", "cost": 3, "atk": 2, "hp": 5, "divine_shield": True,
                        "legendary": True, "icon": "SB"},
    "Little Red Riding Hood": {"type": "minion", "cost": 4, "atk": 3, "hp": 5, "charge": True,
                               "legendary": True, "icon": "LR"},
    "Rumpelstiltskin": {"type": "minion", "cost": 5, "atk": 4, "hp": 4,
                        "deathrattle": {"effect": "dmg_hero", "val": 3},
                        "legendary": True, "icon": "RU"},
    "The Big Bad Wolf": {"type": "minion", "cost": 5, "atk": 5, "hp": 2, "charge": True,
                         "poisonous": True, "legendary": True, "icon": "BW"},
    "Pied Piper": {"type": "minion", "cost": 4, "atk": 3, "hp": 5,
                   "battlecry": {"effect": "draw_cards", "val": 1},
                   "legendary": True, "icon": "PP"},
    "Baba Yaga": {"type": "minion", "cost": 6, "atk": 5, "hp": 5, "poisonous": True,
                  "legendary": True, "icon": "BY"},
    "Bluebeard": {"type": "minion", "cost": 5, "atk": 5, "hp": 4, "taunt": True,
                  "legendary": True, "icon": "BB"},
    "King Arthur": {"type": "minion", "cost": 7, "atk": 6, "hp": 8, "taunt": True,
                   "legendary": True, "icon": "KA"},
    "Merlin": {"type": "minion", "cost": 6, "atk": 4, "hp": 7,
               "battlecry": {"effect": "heal_hero", "val": 6},
               "legendary": True, "icon": "ME"},
    "Lancelot": {"type": "minion", "cost": 5, "atk": 5, "hp": 3, "charge": True,
                 "legendary": True, "icon": "LT"},
    "Guinevere": {"type": "minion", "cost": 4, "atk": 3, "hp": 6, "divine_shield": True,
                  "legendary": True, "icon": "GV"},
    "Morgan le Fay": {"type": "minion", "cost": 6, "atk": 5, "hp": 6, "divine_shield": True,
                      "legendary": True, "icon": "MF"},
    "Mordred": {"type": "minion", "cost": 6, "atk": 6, "hp": 4,
                "deathrattle": {"effect": "dmg_hero", "val": 3},
                "legendary": True, "icon": "MD"},
    "Gawain": {"type": "minion", "cost": 5, "atk": 4, "hp": 6, "taunt": True,
               "legendary": True, "icon": "GW"},
    "Robin Hood": {"type": "minion", "cost": 4, "atk": 4, "hp": 3, "charge": True,
                   "legendary": True, "icon": "RH"},
    "Maid Marian": {"type": "minion", "cost": 3, "atk": 3, "hp": 4,
                    "battlecry": {"effect": "heal_hero", "val": 3},
                    "legendary": True, "icon": "MM"},
    "Friar Tuck": {"type": "minion", "cost": 4, "atk": 3, "hp": 6, "taunt": True,
                   "legendary": True, "icon": "FT"},
    "Little John": {"type": "minion", "cost": 4, "atk": 4, "hp": 5, "taunt": True,
                    "legendary": True, "icon": "LJ"},
    "Will Scarlet": {"type": "minion", "cost": 3, "atk": 3, "hp": 2, "charge": True,
                     "legendary": True, "icon": "WS"},
    "Ebenezer Scrooge": {"type": "minion", "cost": 5, "atk": 3, "hp": 7,
                         "battlecry": {"effect": "draw_cards", "val": 2},
                         "legendary": True, "icon": "ES"},
    "Oliver Twist": {"type": "minion", "cost": 3, "atk": 3, "hp": 3,
                     "battlecry": {"effect": "draw_cards", "val": 1},
                     "legendary": True, "icon": "OT"},

    # ---------- Literary support spells ----------
    "Library Whisper": {"type": "spell",  "cost": 1, "effect": "draw",       "val": 1, "icon": "LW"},
    "Nevermore":       {"type": "spell",  "cost": 3, "effect": "damage",     "val": 4, "icon": "NV"},
    "Elixir of Life":  {"type": "spell",  "cost": 2, "effect": "heal",       "val": 4, "icon": "EL"},
    "Rallying Banner": {"type": "spell",  "cost": 3, "effect": "buff_all",   "val": [1, 1], "icon": "RL"},
    "Circle of Mending": {"type": "spell", "cost": 3, "effect": "heal_all",  "val": 3, "icon": "CM"},
    "Enchanted Shield": {"type": "spell", "cost": 1, "effect": "add_shield", "val": 1, "icon": "EN"},
    "Inkwell Blast":    {"type": "spell", "cost": 2, "effect": "damage_all", "val": 1, "icon": "IB"},
    "Tome of Silence":  {"type": "spell", "cost": 3, "effect": "silence",    "val": 0, "icon": "TS"},

    # ---------- New legendary minions ----------
    "Ivanhoe":          {"type": "minion", "cost": 5, "atk": 4, "hp": 5, "taunt": True, "divine_shield": True,
                         "legendary": True, "icon": "IH"},
    "Quasimodo":        {"type": "minion", "cost": 4, "atk": 2, "hp": 7, "taunt": True,
                         "battlecry": {"effect": "heal_hero", "val": 2},
                         "legendary": True, "icon": "QS"},
    "Don Quixote":      {"type": "minion", "cost": 3, "atk": 4, "hp": 2, "charge": True,
                         "legendary": True, "icon": "DQ"},

    # ---------- Mage class cards ----------
    "Novice Pyromancer": {"type": "minion", "cost": 1, "atk": 1, "hp": 2, "classes": ["Mage"], "icon": "NP"},
    "Ember Archivist":   {"type": "minion", "cost": 2, "atk": 3, "hp": 2, "classes": ["Mage"], "icon": "EA"},
    "Mirror Maiden":     {"type": "minion", "cost": 3, "atk": 2, "hp": 3, "divine_shield": True,
                          "classes": ["Mage"], "icon": "MK"},
    "Sage of Sparks":    {"type": "minion", "cost": 4, "atk": 3, "hp": 5,
                          "battlecry": {"effect": "draw_cards", "val": 1}, "classes": ["Mage"], "icon": "SK"},
    "Scorching Sonnet":  {"type": "spell", "cost": 2, "effect": "damage", "val": 3, "classes": ["Mage"], "icon": "SN"},
    "Arcane Lexicon":    {"type": "spell", "cost": 3, "effect": "draw", "val": 2, "classes": ["Mage"], "icon": "AX"},
    "Arcane Mist":       {"type": "spell", "cost": 1, "effect": "damage_all", "val": 1, "classes": ["Mage"], "icon": "AM"},
    "Meteor Manuscript": {"type": "spell", "cost": 5, "effect": "damage", "val": 7, "classes": ["Mage"], "icon": "MT"},

    # ---------- Warrior class cards ----------
    "Bulwark Bearer":      {"type": "minion", "cost": 2, "atk": 1, "hp": 4, "taunt": True,
                            "classes": ["Warrior"], "icon": "BK"},
    "Shieldwall Sergeant": {"type": "minion", "cost": 3, "atk": 2, "hp": 4, "taunt": True,
                            "divine_shield": True, "classes": ["Warrior"], "icon": "WG"},
    "Rampart Raider":      {"type": "minion", "cost": 3, "atk": 4, "hp": 3, "classes": ["Warrior"], "icon": "RR"},
    "Berserker's Ballad":  {"type": "minion", "cost": 4, "atk": 5, "hp": 4, "charge": True,
                            "classes": ["Warrior"], "icon": "BZ"},
    "Ironclad Anvil":      {"type": "weapon", "cost": 3, "atk": 3, "durability": 2, "classes": ["Warrior"], "icon": "IA"},
    "War Drums":           {"type": "spell", "cost": 3, "effect": "buff_all", "val": [1, 1],
                            "classes": ["Warrior"], "icon": "WD"},
    "Cleave Chronicle":    {"type": "spell", "cost": 3, "effect": "damage_all", "val": 1, "classes": ["Warrior"], "icon": "CV"},
    "Fortify":             {"type": "spell", "cost": 2, "effect": "heal", "val": 5, "classes": ["Warrior"], "icon": "FY"},

    # ---------- Priest class cards ----------
    "Humble Acolyte":      {"type": "minion", "cost": 1, "atk": 1, "hp": 3, "classes": ["Priest"], "icon": "HA"},
    "Blessed Bibliophile": {"type": "minion", "cost": 2, "atk": 2, "hp": 3,
                            "battlecry": {"effect": "heal_hero", "val": 2}, "classes": ["Priest"], "icon": "BI"},
    "Radiant Chaplain":    {"type": "minion", "cost": 3, "atk": 3, "hp": 4, "divine_shield": True,
                            "classes": ["Priest"], "icon": "RC"},
    "Cathedral Protector": {"type": "minion", "cost": 5, "atk": 4, "hp": 6, "taunt": True,
                            "classes": ["Priest"], "icon": "CP"},
    "Sacred Salve":        {"type": "spell", "cost": 2, "effect": "heal", "val": 4, "classes": ["Priest"], "icon": "SS"},
    "Smite Scripture":     {"type": "spell", "cost": 3, "effect": "damage", "val": 4, "classes": ["Priest"], "icon": "SM"},
    "Hymn of Hope":        {"type": "spell", "cost": 4, "effect": "heal_all", "val": 4, "classes": ["Priest"], "icon": "HH"},
    "Greater Restoration": {"type": "spell", "cost": 5, "effect": "heal", "val": 8, "classes": ["Priest"], "icon": "GR"},

    # ---------- Rogue class cards ----------
    "Back Alley Burglar": {"type": "minion", "cost": 1, "atk": 2, "hp": 1, "charge": True,
                          "classes": ["Rogue"], "icon": "BA"},
    "Shadowstep Scout":   {"type": "minion", "cost": 2, "atk": 3, "hp": 2, "classes": ["Rogue"], "icon": "SC"},
    "Venomous Valet":     {"type": "minion", "cost": 4, "atk": 3, "hp": 3, "poisonous": True,
                          "classes": ["Rogue"], "icon": "VV"},
    "Thief's Shiv":       {"type": "weapon", "cost": 1, "atk": 1, "durability": 2, "classes": ["Rogue"], "icon": "TV"},
    "Assassin's Rapier":  {"type": "weapon", "cost": 5, "atk": 3, "durability": 4, "classes": ["Rogue"], "icon": "AR"},
    "Cheap Shot":         {"type": "spell", "cost": 2, "effect": "damage", "val": 2, "classes": ["Rogue"], "icon": "KT"},
    "Shiv Storm":         {"type": "spell", "cost": 2, "effect": "damage_all", "val": 1, "classes": ["Rogue"], "icon": "SV"},
    "Heist Ledger":       {"type": "spell", "cost": 4, "effect": "draw", "val": 3, "classes": ["Rogue"], "icon": "HL"},

    # ---------- Paladin class cards ----------
    "Squire of Light":      {"type": "minion", "cost": 1, "atk": 1, "hp": 1, "taunt": True,
                             "divine_shield": True, "classes": ["Paladin"], "icon": "SL"},
    "Silver Dawn Knight":   {"type": "minion", "cost": 2, "atk": 3, "hp": 2, "divine_shield": True,
                             "classes": ["Paladin"], "icon": "DK"},
    "Crusader's Charge":    {"type": "minion", "cost": 3, "atk": 3, "hp": 1, "charge": True,
                             "divine_shield": True, "classes": ["Paladin"], "icon": "CR"},
    "Truesilver Testament": {"type": "weapon", "cost": 4, "atk": 4, "durability": 2, "classes": ["Paladin"], "icon": "TU"},
    "Holy Wrath Scroll":    {"type": "spell", "cost": 2, "effect": "damage", "val": 3, "classes": ["Paladin"], "icon": "HS"},
    "Kings' Decree":        {"type": "spell", "cost": 4, "effect": "buff", "val": [4, 4], "classes": ["Paladin"], "icon": "KD"},
    "Consecration Psalm":   {"type": "spell", "cost": 3, "effect": "damage_all", "val": 2, "classes": ["Paladin"], "icon": "PS"},
    "Lay on Hands":         {"type": "spell", "cost": 5, "effect": "heal", "val": 8, "classes": ["Paladin"], "icon": "LH"},

    # ---------- Shaman class cards ----------
    "Spirit Wolf":        {"type": "minion", "cost": 2, "atk": 2, "hp": 2, "charge": True,
                          "classes": ["Shaman"], "icon": "WL"},
    "Thunder Totemist":   {"type": "minion", "cost": 3, "atk": 3, "hp": 3, "classes": ["Shaman"], "icon": "TN"},
    "Flame Totem Keeper":{"type": "minion", "cost": 2, "atk": 2, "hp": 3, "classes": ["Shaman"], "icon": "FK"},
    "Stormhammer Saga":   {"type": "weapon", "cost": 2, "atk": 2, "durability": 3, "classes": ["Shaman"], "icon": "HM"},
    "Lightning Limerick": {"type": "spell", "cost": 1, "effect": "damage", "val": 3, "classes": ["Shaman"], "icon": "LL"},
    "Maelstrom Verse":    {"type": "spell", "cost": 3, "effect": "damage_all", "val": 2, "classes": ["Shaman"], "icon": "MV"},
    "Hex of Baba":        {"type": "spell", "cost": 3, "effect": "silence", "val": 0, "classes": ["Shaman"], "icon": "HX"},
    "Ancestral Memory":   {"type": "spell", "cost": 2, "effect": "draw", "val": 2, "classes": ["Shaman"], "icon": "AN"},

    # ---------- Uncollectible ----------
    COIN_CARD: {"type": "spell", "cost": 0, "effect": "coin", "val": 1,
                "icon": "CN", "uncollectible": True},
}

HERO_CLASSES = ["Mage", "Warrior", "Priest", "Rogue", "Paladin", "Shaman"]

SHAMAN_TOTEMS = [
    {"name": "Searing Totem", "type": "minion", "cost": 0, "atk": 1, "hp": 1, "icon": "ST"},
    {"name": "Healing Totem", "type": "minion", "cost": 0, "atk": 0, "hp": 2, "icon": "HE"},
    {"name": "Stonefang Totem", "type": "minion", "cost": 0, "atk": 0, "hp": 2, "taunt": True, "icon": "SF"},
    {"name": "Wrath of Air Totem", "type": "minion", "cost": 0, "atk": 0, "hp": 2, "icon": "WA"},
]


def card_max_copies(name: str) -> int:
    return 1 if CARD_DB[name].get("legendary") else 2


def card_allowed_for_class(card_name: str, hero_class: str) -> bool:
    """True if a collectable card may appear in a deck for hero_class."""
    card = CARD_DB.get(card_name)
    if not card or card.get("uncollectible"):
        return False
    classes = card.get("classes")
    if not classes:
        return True
    return hero_class in classes


def cards_for_class(hero_class: str) -> list[str]:
    """Collectable card names legal in a deck for the given hero class."""
    return [n for n in CARD_DB if card_allowed_for_class(n, hero_class)]


AI_DIFFICULTIES = ("easy", "normal", "hard")

# Target copies per mana bucket for AI deck curves (sums to DECK_SIZE).
CURVE_TARGETS = {1: 4, 2: 8, 3: 8, 4: 6, 5: 3, 6: 1}

CAMPAIGN_NODES = [
    {
        "id": "n1",
        "name": "Street Urchin",
        "subtitle": "A quick-fingered Rogue tests your opener.",
        "difficulty": "easy",
        "ai_class": "Rogue",
    },
    {
        "id": "n2",
        "name": "Town Guard",
        "subtitle": "Taunts and shields slow your assault.",
        "difficulty": "normal",
        "ai_class": "Warrior",
    },
    {
        "id": "n3",
        "name": "Guild Librarian",
        "subtitle": "Arcane tricks and burn spells.",
        "difficulty": "normal",
        "ai_class": "Mage",
    },
    {
        "id": "n4",
        "name": "Victor Frankenstein",
        "subtitle": "Mad science — monsters, heals, and stubborn taunts.",
        "difficulty": "hard",
        "boss_id": "frankenstein",
    },
    {
        "id": "n5",
        "name": "Van Helsing",
        "subtitle": "Elite hunter — charges and armor.",
        "difficulty": "hard",
        "boss_id": "van_helsing",
    },
    {
        "id": "n6",
        "name": "Professor Moriarty",
        "subtitle": "Final boss — poison, daggers, and schemes.",
        "difficulty": "hard",
        "boss_id": "moriarty",
    },
]

BOSS_PRESETS = {
    "frankenstein": {
        "display_name": "Victor Frankenstein",
        "hero_class": "Priest",
        "hp": 33,
        "core": [
            "Victor Frankenstein", "Frankenstein's Monster",
            "Humble Acolyte", "Humble Acolyte",
            "Cathedral Cleric", "Cathedral Cleric",
            "Castle Guard", "Castle Guard", "Radiant Chaplain", "Radiant Chaplain",
            "Restorative Hymn", "Elixir of Life", "Sacred Salve", "Sacred Salve",
            "Smite Scripture", "Smite Scripture", "Hymn of Hope",
            "Greater Restoration", "Templar Captain", "Templar Captain",
            "Errant Knight", "Errant Knight", "Highwayman", "Highwayman",
            "Blessed Bibliophile", "Blessed Bibliophile", "Inkwell Blast", "Inkwell Blast",
            "Cathedral Protector", "Castle Guard",
        ],
    },

    "van_helsing": {
        "display_name": "Van Helsing",
        "hero_class": "Warrior",
        "hp": 35,
        "core": [
            "Van Helsing", "Gawain", "Gawain", "Lancelot", "Lancelot",
            "Errant Knight", "Errant Knight", "Castle Guard", "Castle Guard",
            "Templar Captain", "Bulwark Bearer", "Bulwark Bearer",
            "Shieldwall Sergeant", "Shieldwall Sergeant", "Rampart Raider", "Rampart Raider",
            "Cleave Chronicle", "Cleave Chronicle", "Fortify", "Fortify",
            "War Drums", "Ironclad Anvil", "Bulwark Bearer", "Rampart Raider",
            "Castle Guard", "Errant Knight", "Gawain", "Lancelot", "Fortify", "Cleave Chronicle",
        ],
    },
    "moriarty": {
        "display_name": "Professor Moriarty",
        "hero_class": "Rogue",
        "hp": 32,
        "core": [
            "Professor Moriarty", "Back Alley Burglar", "Back Alley Burglar",
            "Shadowstep Scout", "Shadowstep Scout", "Venomous Valet", "Venomous Valet",
            "Sherlock Holmes", "Cheap Shot", "Cheap Shot", "Shiv Storm", "Shiv Storm",
            "Thief's Shiv", "Thief's Shiv", "Assassin's Rapier", "Heist Ledger", "Heist Ledger",
            "Cave Spider", "Cave Spider", "Rebel's Ambush", "Quill Bolt", "Quill Bolt",
            "Back Alley Burglar", "Shadowstep Scout", "Cheap Shot", "Shiv Storm",
            "Venomous Valet", "Heist Ledger", "Thief's Shiv", "Rebel's Ambush",
        ],
    },
}


def get_campaign_node(node_id: str) -> dict | None:
    for node in CAMPAIGN_NODES:
        if node["id"] == node_id:
            return node
    return None


def complete_deck_from_core(hero_class: str, core: list[str]) -> list[str]:
    """Build a legal DECK_SIZE deck starting from themed core cards."""
    deck: list[str] = []
    for name in core:
        if len(deck) >= DECK_SIZE:
            break
        if name not in CARD_DB or not card_allowed_for_class(name, hero_class):
            continue
        if deck.count(name) < card_max_copies(name):
            deck.append(name)
    for name in build_curved_ai_deck(hero_class):
        if len(deck) >= DECK_SIZE:
            break
        if deck.count(name) < card_max_copies(name):
            deck.append(name)
    return deck[:DECK_SIZE]


def build_curved_ai_deck(hero_class: str) -> list[str]:
    """Build a 30-card deck with a playable mana curve for the AI."""
    pool = [n for n in cards_for_class(hero_class) if not CARD_DB[n].get("legendary")]
    by_cost: dict[int, list[str]] = {}
    for name in pool:
        cost = max(1, min(CARD_DB[name]["cost"], 6))
        by_cost.setdefault(cost, []).append(name)

    deck: list[str] = []

    def try_add(name: str) -> bool:
        if len(deck) >= DECK_SIZE:
            return False
        if deck.count(name) >= card_max_copies(name):
            return False
        deck.append(name)
        return True

    for cost, need in CURVE_TARGETS.items():
        added = 0
        candidates = list(by_cost.get(cost, []))
        random.shuffle(candidates)
        for name in candidates:
            while try_add(name) and added < need:
                added += 1
            if added >= need:
                break
        if added < need:
            for alt in (cost - 1, cost + 1, cost - 2, cost + 2):
                if alt < 1 or alt > 6:
                    continue
                for name in by_cost.get(alt, []):
                    while try_add(name) and added < need:
                        added += 1
                    if added >= need:
                        break
                if added >= need:
                    break

    guard = 0
    shuffled = list(pool)
    random.shuffle(shuffled)
    while len(deck) < DECK_SIZE and guard < DECK_SIZE * 4:
        guard += 1
        try_add(shuffled[guard % len(shuffled)])
    return deck[:DECK_SIZE]


def create_ai_opponent(
    *,
    hero_class: str | None = None,
    boss_id: str | None = None,
    campaign_node: str | None = None,
) -> dict:
    """Create an AI player with a curved or scripted deck."""
    if boss_id and boss_id in BOSS_PRESETS:
        preset = BOSS_PRESETS[boss_id]
        hero_class = preset["hero_class"]
        deck = complete_deck_from_core(hero_class, preset["core"])
        player = create_player(preset["display_name"], hero_class, deck)
        boss_hp = preset.get("hp", 30)
        player["hp"] = boss_hp
        player["max_hp"] = boss_hp
        return player

    ai_class = hero_class or "Mage"
    if campaign_node:
        node = get_campaign_node(campaign_node)
        if node and not boss_id:
            ai_class = node.get("ai_class", ai_class)

    deck = build_curved_ai_deck(ai_class)
    return create_player("AI", ai_class, deck)


def normalize_difficulty(difficulty: str | None) -> str:
    d = (difficulty or "normal").lower()
    return d if d in AI_DIFFICULTIES else "normal"


def select_ai_move(
    legal: list,
    p2: dict,
    p1: dict,
    difficulty: str = "normal",
) -> tuple | None:
    """Pick a move for the AI based on difficulty tier."""
    if not legal:
        return None

    scored = [(evaluate_ai_move(p2, p1, mv), mv) for mv in legal]
    scored.sort(key=lambda pair: -pair[0])

    if difficulty == "easy":
        if random.random() < 0.4:
            return random.choice(legal)
        pool = scored[: max(1, (len(scored) + 1) // 2)]
        return random.choice(pool)[1]

    best_score = scored[0][0]
    if best_score < 0:
        return scored[-1][1]

    if difficulty == "hard":
        contenders = [mv for score, mv in scored if score >= best_score - 1.5]
        return max(contenders, key=lambda mv: evaluate_ai_move(p2, p1, mv))

    # normal — slight variety among near-best lines
    contenders = [mv for score, mv in scored if score >= best_score - 0.75]
    return random.choice(contenders)


GAME_LOG: list[str] = []
_ACTIVE_LOG: list[str] | None = None


def set_active_log(log: list[str] | None) -> None:
    """Route log_action output to a per-game log list (used by the server)."""
    global _ACTIVE_LOG
    _ACTIVE_LOG = log


def get_spell_desc(card: dict, short: bool = False) -> str:
    e, v = card.get("effect"), card.get("val")
    if e == "coin":       return "+1 Mana"                  if short else "Gain 1 Mana Crystal this turn only."
    if e == "damage":     return f"Deal {v} Dmg"            if short else f"Deal {v} damage."
    if e == "heal":       return f"Heal {v} HP"             if short else f"Restore {v} HP."
    if e == "draw":       return f"Draw {v} Cards"          if short else f"Draw {v} cards."
    if e == "damage_all": return f"AoE Dmg {v}"             if short else f"Deal {v} dmg to all enemy minions."
    if e == "buff":       return f"Buff +{v[0]}/+{v[1]}"   if short else f"Give a minion +{v[0]}/+{v[1]}."
    if e == "buff_all":   return f"Buff All +{v[0]}/+{v[1]}" if short else f"Give all friendly minions +{v[0]}/+{v[1]}."
    if e == "heal_all":   return f"Heal All {v} HP"         if short else f"Restore {v} HP to all friendly characters."
    if e == "add_shield": return "Add Shield"               if short else "Give a friendly minion Divine Shield."
    if e == "silence":    return "Silence"                  if short else "Remove all text from an enemy minion."
    return ""


def get_battlecry_desc(battlecry: dict | None) -> str:
    if not battlecry:
        return ""
    effect, val = battlecry.get("effect"), battlecry.get("val")
    if effect == "heal_hero":
        return f"Battlecry: Restore {val} HP to your hero."
    if effect == "draw_cards":
        suffix = "s" if val != 1 else ""
        return f"Battlecry: Draw {val} card{suffix}."
    return ""


def get_deathrattle_desc(deathrattle: dict | None) -> str:
    if not deathrattle:
        return ""
    if deathrattle.get("effect") == "dmg_hero":
        return f"Deathrattle: Deal {deathrattle['val']} damage to the enemy hero."
    return ""


def enrich_card(card: dict) -> dict:
    """Attach display text for API / client consumption."""
    enriched = dict(card)
    if card.get("type") == "spell":
        enriched["desc_short"] = get_spell_desc(card, short=True)
        enriched["desc_long"] = get_spell_desc(card, short=False)
    bc = card.get("battlecry")
    if bc:
        enriched["battlecry_text"] = get_battlecry_desc(bc)
    dr = card.get("deathrattle")
    if dr:
        enriched["deathrattle_text"] = get_deathrattle_desc(dr)
    return enriched


def collectible_card_db() -> dict[str, dict]:
    return {
        name: enrich_card(card)
        for name, card in CARD_DB.items()
        if not card.get("uncollectible")
    }


def log_action(msg: str) -> None:
    GAME_LOG.append(msg)
    if _ACTIVE_LOG is not None:
        _ACTIVE_LOG.append(msg)


# ---------------------------------------------------------------------------
# 2. STATE INITIALISATION
# ---------------------------------------------------------------------------

def clamp_practice_hp(value, default: int = 30) -> int:
    """Clamp custom hero HP for practice sandbox (1–60)."""
    try:
        hp = int(value)
    except (TypeError, ValueError):
        return default
    return max(1, min(60, hp))


def apply_practice_options(player: dict, *, hp: int, infinite_mana: bool = False) -> None:
    """Apply practice-mode sandbox flags to a player."""
    player["hp"] = clamp_practice_hp(hp)
    player["max_hp"] = player["hp"]
    if infinite_mana:
        player["infinite_mana"] = True
        player["max_mana"] = MAX_MANA
        player["mana"] = MAX_MANA


def refresh_infinite_mana(player: dict) -> None:
    if player.get("infinite_mana"):
        player["max_mana"] = MAX_MANA
        player["mana"] = MAX_MANA


def effective_mana(player: dict) -> int:
    return MAX_MANA if player.get("infinite_mana") else player["mana"]


def clamp_heal(player: dict, amount: int) -> int:
    """Heal amount capped by hero max_hp."""
    cap = player.get("max_hp", DEFAULT_HERO_HP)
    return max(0, min(amount, cap - player["hp"]))


def create_player(name: str, hero_class: str = "Mage",
                  custom_deck: list | None = None, shuffle: bool = True) -> dict:
    if custom_deck is not None:
        deck = custom_deck.copy()
    else:
        deck = build_curved_ai_deck(hero_class)
    if shuffle:
        random.shuffle(deck)
    return {
        "name":            name,
        "hero_class":      hero_class,
        "hp":              DEFAULT_HERO_HP,
        "max_hp":          DEFAULT_HERO_HP,
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
        "hero_attacked_this_turn": False,
    }


def draw_card(player: dict, on_event=None) -> None:
    if player["deck"]:
        if len(player["hand"]) < MAX_HAND_SIZE:
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


def start_turn(player: dict, on_event=None, *, draw: bool = True) -> None:
    refresh_infinite_mana(player)
    if not player.get("infinite_mana"):
        if player["max_mana"] < MAX_MANA:
            player["max_mana"] += 1
        player["mana"] = player["max_mana"]
    player["hero_power_used"] = False
    player["hero_attacked_this_turn"] = False
    player["hero_can_attack"] = bool(player["weapon"])
    for m in player["board"]:
        m["can_attack"] = True
    if draw:
        draw_card(player, on_event)


def give_coin(player: dict) -> None:
    """Grant The Coin to the player going second."""
    player["hand"].append(COIN_CARD)
    log_action(f"{player['name']} receives {COIN_CARD}!")


def ai_choose_mulligan(player: dict) -> list[int]:
    """Heuristic mulligan: keep early curve, replace expensive dead cards."""
    swap: list[int] = []
    costs: list[int] = []
    for i, card_name in enumerate(player["hand"]):
        card = CARD_DB[card_name]
        cost = card.get("cost", 0)
        costs.append(cost)
        if cost >= 5:
            swap.append(i)
        elif cost == 4 and len(player["hand"]) >= 4:
            swap.append(i)

    kept = [c for j, c in enumerate(costs) if j not in swap]
    if kept:
        has_early = any(c <= 2 for c in kept)
        if not has_early and max(kept) >= 3:
            for i, cost in enumerate(costs):
                if cost >= 3 and i not in swap:
                    swap.append(i)
        # Two or more 5+ cards is too greedy for an opener.
        if sum(1 for c in kept if c >= 5) >= 2:
            for i, cost in enumerate(costs):
                if cost >= 5 and i not in swap:
                    swap.append(i)
    return sorted(set(swap))


def ai_do_mulligan(player: dict) -> list[int]:
    """Run the AI mulligan and return swapped indices."""
    indices = ai_choose_mulligan(player)
    if indices:
        log_action(f"{player['name']} mulligans {len(indices)} card(s).")
        do_mulligan(player, indices)
    else:
        log_action(f"{player['name']} keeps their opening hand.")
    return indices


def do_mulligan(player: dict, swap_indices: list) -> None:
    """Swap selected hand cards back into the deck and draw replacements.

    Replacement cards are drawn first (from the existing deck), then the
    swapped cards are shuffled back in.  This guarantees the player can never
    be redealt the exact cards they just chose to swap away.
    Cards NOT in swap_indices are kept unchanged.
    """
    if not swap_indices:
        return
    # Gather cards to swap (removing from hand in reverse-index order)
    to_swap = []
    for i in sorted(set(swap_indices), reverse=True):
        if 0 <= i < len(player["hand"]):
            to_swap.append(player["hand"].pop(i))
    # Draw replacements BEFORE returning the swapped cards so they cannot
    # appear in the replacement draws.
    for _ in range(len(to_swap)):
        draw_card(player)
    # Return swapped cards to random positions in the deck
    for card in to_swap:
        insert_pos = random.randint(0, len(player["deck"]))
        player["deck"].insert(insert_pos, card)


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
    if player["hp"] <= 0 or opp["hp"] <= 0:
        return []

    moves = []

    for hand_idx, card_name in enumerate(player["hand"]):
        card = CARD_DB[card_name]
        if effective_mana(player) < card["cost"]:
            continue
        if card["type"] == "minion":
            if len(player["board"]) < MAX_BOARD_SIZE:
                moves.append(("play", hand_idx, None))
        elif card["type"] == "spell":
            if card["effect"] in ("heal", "draw", "damage_all", "buff_all", "heal_all", "coin"):
                moves.append(("play", hand_idx, None))
            elif card["effect"] == "damage":
                for t in get_valid_targets(opp, is_attack=False):
                    moves.append(("play", hand_idx, t))
            elif card["effect"] in ("buff", "add_shield"):
                for t in range(len(player["board"])):
                    moves.append(("play", hand_idx, t))
            elif card["effect"] == "silence":
                for t in range(len(opp["board"])):
                    moves.append(("play", hand_idx, t))
        elif card["type"] == "weapon":
            moves.append(("play", hand_idx, None))

    valid_targets = get_valid_targets(opp, is_attack=True)
    for bi, minion in enumerate(player["board"]):
        if minion.get("can_attack"):
            for t in valid_targets:
                moves.append(("attack", bi, t))

    if (
        player["weapon"]
        and player["hero_can_attack"]
        and not player.get("hero_attacked_this_turn")
    ):
        for t in valid_targets:
            moves.append(("hero_attack", None, t))

    if effective_mana(player) >= 2 and not player["hero_power_used"]:
        cls = player["hero_class"]
        if cls == "Warrior":
            moves.append(("hero_power", None, None))
        elif cls == "Mage":
            for t in get_valid_targets(opp, is_attack=False):
                moves.append(("hero_power", None, t))
        elif cls == "Priest":
            for t in ["hero"] + list(range(len(player["board"]))):
                moves.append(("hero_power", None, t))
        elif cls == "Rogue":
            moves.append(("hero_power", None, None))
        elif cls == "Paladin":
            if len(player["board"]) < MAX_BOARD_SIZE:
                moves.append(("hero_power", None, None))
        elif cls == "Shaman":
            if len(player["board"]) < MAX_BOARD_SIZE:
                moves.append(("hero_power", None, None))

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
        if not player.get("infinite_mana"):
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
                    amt = clamp_heal(player, bc["val"])
                    player["hp"] += amt
                    log_action(f"   [B.CRY] Battlecry: Heals hero for {amt}!")
                    notify("heal", player, "hero", amt)
                elif bc["effect"] == "draw_cards":
                    log_action(f"   [B.CRY] Battlecry: {player['name']} draws {bc['val']} card(s)!")
                    for _ in range(bc["val"]):
                        draw_card(player, on_event)

        elif card["type"] == "weapon":
            player["weapon"] = {"name": card_name, "atk": card["atk"],
                                 "durability": card["durability"]}
            if not player.get("hero_attacked_this_turn"):
                player["hero_can_attack"] = True
            log_action(f"   Equipped {card_name} ({card['atk']} Atk / {card['durability']} Durability).")

        elif card["type"] == "spell":
            if card["effect"] == "coin":
                player["mana"] += card["val"]
                log_action(f"   {player['name']} gains {card['val']} mana this turn!")
                notify("heal", player, "hero", 0)

            elif card["effect"] == "heal":
                amt = clamp_heal(player, card["val"])
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
                        log_action(f"   {tm['name']} takes {card['val']} damage.")
                        notify("damage", opp, i, card["val"])

            elif card["effect"] == "buff":
                if target is None or not (0 <= target < len(player["board"])):
                    log_action(f"   [ERROR] {card_name} target out of range — card wasted!")
                    cleanup_dead(player, opp, on_event)
                    return
                tm = player["board"][target]
                tm["max_hp"]  = tm.get("max_hp", tm["hp"]) + card["val"][1]
                tm["atk"]    += card["val"][0]
                tm["hp"]     += card["val"][1]
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

            elif card["effect"] == "buff_all":
                log_action(f"   {player['name']} rallies all minions with +{card['val'][0]}/+{card['val'][1]}!")
                for i, tm in enumerate(player["board"]):
                    tm["max_hp"] = tm.get("max_hp", tm["hp"]) + card["val"][1]
                    tm["atk"]   += card["val"][0]
                    tm["hp"]    += card["val"][1]
                    notify("heal", player, i, card["val"][1])

            elif card["effect"] == "heal_all":
                log_action(f"   {player['name']} mends all friendly characters for {card['val']} HP!")
                amt_hero = clamp_heal(player, card["val"])
                player["hp"] += amt_hero
                if amt_hero:
                    notify("heal", player, "hero", amt_hero)
                for i, tm in enumerate(player["board"]):
                    max_hp = tm.get("max_hp", tm["hp"])
                    amt = max(0, min(card["val"], max_hp - tm["hp"]))
                    tm["hp"] += amt
                    if amt:
                        notify("heal", player, i, amt)

            elif card["effect"] == "add_shield":
                if target is None or not (0 <= target < len(player["board"])):
                    log_action(f"   [ERROR] {card_name} target out of range — card wasted!")
                    cleanup_dead(player, opp, on_event)
                    return
                tm = player["board"][target]
                tm["divine_shield"] = True
                log_action(f"   {player['name']} grants Divine Shield to {tm['name']}!")
                notify("heal", player, target, 0)

            elif card["effect"] == "silence":
                if target is None or not (0 <= target < len(opp["board"])):
                    log_action(f"   [ERROR] {card_name} target out of range — card wasted!")
                    cleanup_dead(player, opp, on_event)
                    return
                tm = opp["board"][target]
                for kw in MINION_TRAITS:
                    tm.pop(kw, None)
                log_action(f"   [SILENCE] {tm['name']} is silenced! All effects removed.")
                notify("blocked", opp, target, "SILENCED!")

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
            log_action(f">> {attacker['name']} attacks {defender['name']} for {attacker['atk']} damage!")

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

            if defender["atk"] > 0:
                if attacker.get("divine_shield"):
                    attacker["divine_shield"] = False
                    log_action(f"   {attacker['name']}'s Divine Shield blocks retaliation!")
                    notify("blocked", player, idx, "BLOCKED!")
                else:
                    attacker["hp"] -= defender["atk"]
                    notify("damage", player, idx, defender["atk"])
                    log_action(f"   {attacker['name']} takes {defender['atk']} retaliation damage.")
                    if defender.get("poisonous"):
                        attacker["hp"] = 0
                        log_action(f"   [POISON] Poisonous destroys {attacker['name']}!")

    # ---- HERO ATTACK --------------------------------------------------------
    elif action == "hero_attack":
        player["hero_attacked_this_turn"] = True
        player["hero_can_attack"] = False
        weapon = player["weapon"]
        w_atk  = weapon["atk"]

        if target == "hero":
            damage_hero(opp, w_atk)
            log_action(f">> {player['name']} attacks {opp['name']} with {weapon['name']} for {w_atk} dmg!")
            notify("damage", opp, "hero", w_atk)
        else:
            defender = opp["board"][target]
            log_action(f">> {player['name']} attacks {defender['name']} with {weapon['name']} for {w_atk} damage!")
            if defender.get("divine_shield"):
                defender["divine_shield"] = False
                log_action(f"   {defender['name']}'s Divine Shield blocks the attack!")
                notify("blocked", opp, target, "BLOCKED!")
            else:
                defender["hp"] -= w_atk
                notify("damage", opp, target, w_atk)
            if defender["atk"] > 0:
                damage_hero(player, defender["atk"])
                notify("damage", player, "hero", defender["atk"])
                log_action(f"   {player['name']}'s hero takes {defender['atk']} retaliation damage.")

        weapon["durability"] -= 1
        if weapon["durability"] <= 0:
            log_action(f"   {player['name']}'s {weapon['name']} breaks!")
            player["weapon"] = None

    # ---- HERO POWER ---------------------------------------------------------
    elif action == "hero_power":
        if not player.get("infinite_mana"):
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
                amt = clamp_heal(player, 2)
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

        elif cls == "Rogue":
            # Dagger Mastery: equip (or refresh) a 1/2 Wicked Dagger
            player["weapon"] = {"name": "Wicked Dagger", "atk": 1, "durability": 2}
            if not player.get("hero_attacked_this_turn"):
                player["hero_can_attack"] = True
            log_action(f">> {player['name']} uses Dagger Mastery! Equipped a 1/2 Wicked Dagger.")
            notify("armor", player, "hero", 0)

        elif cls == "Paladin":
            # Reinforce: summon a 1/1 Silver Hand Recruit
            recruit = {
                "name": "Silver Hand Recruit", "type": "minion", "cost": 0,
                "atk": 1, "hp": 1, "max_hp": 1, "can_attack": False, "icon": "SR",
            }
            player["board"].append(recruit)
            log_action(f">> {player['name']} uses Reinforce! Summons a 1/1 Silver Hand Recruit.")
            notify("armor", player, "hero", 0)

        elif cls == "Shaman":
            totem_tpl = random.choice(SHAMAN_TOTEMS)
            totem = dict(totem_tpl)
            totem["max_hp"] = totem["hp"]
            totem["can_attack"] = False
            player["board"].append(totem)
            log_action(f">> {player['name']} uses Totemic Call! Summons {totem['name']}.")
            notify("armor", player, "hero", 0)

    refresh_infinite_mana(player)
    cleanup_dead(player, opp, on_event)


def cleanup_dead(player: dict, opp: dict, on_event=None) -> None:
    def process(owner, enemy):
        alive = []
        for m in owner["board"]:
            if m["hp"] > 0:
                alive.append(m)
            else:
                log_action(f"   {m['name']} is destroyed!")
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

def _hero_missing_hp(player: dict) -> int:
    cap = player.get("max_hp", DEFAULT_HERO_HP)
    return max(0, cap - player["hp"])


def _ai_should_pass_turn(legal: list, move: tuple, score: float, p2: dict, p1: dict) -> bool:
    """Stop the AI turn when the chosen move is a wasteful hero power."""
    del legal, p2, p1  # signature kept for future lookahead
    if move[0] == "hero_power" and score <= 0:
        return True
    return False


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
                hp_missing = _hero_missing_hp(p2)
                effective_heal = min(card["val"], hp_missing)
                score += effective_heal if effective_heal > 0 else -3

            elif card["effect"] == "draw":
                score += card["val"] * 4 if len(p2["hand"]) < 9 else -10

            elif card["effect"] == "coin":
                unspent = p2["mana"]
                playable_costs = [
                    CARD_DB[n]["cost"] for n in p2["hand"]
                    if CARD_DB[n].get("cost", 0) > unspent
                ]
                score += 3 if playable_costs else -2

            elif card["effect"] == "damage_all":
                hits = sum(5 if m["hp"] <= card["val"] else 1 for m in p1["board"])
                score += hits * 2 if hits else -10

            elif card["effect"] == "buff":
                score += sum(card["val"]) * 2
                tm = p2["board"][target]
                if tm["can_attack"]: score += card["val"][0] * 3
                if tm["hp"] > 2:     score += 2

            elif card["effect"] == "buff_all":
                n = len(p2["board"])
                score += n * sum(card["val"]) if n else -8

            elif card["effect"] == "heal_all":
                heal_val = card["val"]
                score += 3 if _hero_missing_hp(p2) >= 10 else 0
                score += sum(
                    min(heal_val, m.get("max_hp", m["hp"]) - m["hp"])
                    for m in p2["board"]
                )

            elif card["effect"] == "add_shield":
                tm = p2["board"][target]
                score += tm["atk"] * 2 if tm["can_attack"] else tm["hp"]

            elif card["effect"] == "silence":
                if 0 <= target < len(p1["board"]):
                    tm = p1["board"][target]
                    kw_count = sum(1 for kw in ("taunt", "divine_shield", "poisonous", "deathrattle")
                                   if tm.get(kw))
                    score += kw_count * 6
                    if tm.get("taunt"):    score += 4   # removing taunt opens up better targets
                    if tm.get("divine_shield"): score += 4

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

            if defender.get("taunt") and sum(
                m["atk"] for m in p2["board"] if m.get("can_attack")
            ) > attacker["atk"]:
                score += 4

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
            missing = _hero_missing_hp(p2)
            if missing == 0 and p2.get("armor", 0) >= 8:
                score -= 8
            elif missing == 0:
                score -= 3
            else:
                score += min(4, missing)
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
                healable = clamp_heal(p2, 2)
                score += healable * 2 if healable > 0 else -6
            else:
                tm = p2["board"][target]
                max_hp = tm.get("max_hp", tm["hp"])
                missing = max(0, max_hp - tm["hp"])
                score += min(4, missing) if missing > 0 else -5
        elif cls == "Rogue":
            # Dagger Mastery: equip 1/2 weapon — worth it if no weapon already
            score += 4 if not p2.get("weapon") else -2
        elif cls == "Paladin":
            # Reinforce: always decent if board isn't full
            score += 3 if len(p2["board"]) < 7 else -10
        elif cls == "Shaman":
            score += 3 if len(p2["board"]) < 7 else -10

    return score


def run_ai_turn(
    p2: dict,
    p1: dict,
    max_moves: int = 40,
    *,
    draw: bool = True,
    difficulty: str = "normal",
) -> list[tuple]:
    """Execute AI turn synchronously. Returns the list of moves made."""
    difficulty = normalize_difficulty(difficulty)
    start_turn(p2, draw=draw)
    if check_win(p1, p2):
        return []
    moves_made = []
    for _ in range(max_moves):
        if check_win(p1, p2):
            break
        legal = get_legal_moves(p2, p1)
        if not legal:
            break
        best = select_ai_move(legal, p2, p1, difficulty)
        if best is None:
            break
        best_score = evaluate_ai_move(p2, p1, best)
        if _ai_should_pass_turn(legal, best, best_score, p2, p1):
            break
        execute_move(p2, p1, best)
        moves_made.append(best)
    return moves_made
