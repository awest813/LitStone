# LitStone

A browser-based card game inspired by Hearthstone, built entirely from **public domain literature**.
Heroes, minions, spells, and weapons are drawn from mythology, Gothic novels, and classic fiction — no IP issues, infinite story potential.

## Quick Start

```bash
pip install flask
python server.py
# → open http://localhost:5000
```

Requires Python 3.10+ and Flask 3.x.

## How to Play

1. **Choose a Hero class** — Mage (Fireblast), Warrior (Armor Up), or Priest (Lesser Heal)
2. **Build a 15-card deck** in the deck builder (max 2 copies per card)
3. **Play vs AI** — the opponent plays a smart greedy AI
4. **Win by reducing your opponent's hero to 0 HP**

### Controls

| Action | How |
|---|---|
| Play a card | Click it in your hand |
| Attack with a minion | Click your minion, then click the target |
| Use hero power | Click the circular power button |
| Attack with weapon | Click your hero portrait, then click a target |
| Cancel selection | Right-click or press Escape |
| End turn | Click **End Turn** |

## Current Features (v0.1)

- 16 playable cards across 3 types (minion, spell, weapon)
- 3 hero classes with unique hero powers
- Full keyword system: Taunt, Divine Shield, Charge, Poisonous, Battlecry, Deathrattle
- Deck builder with card pool and copy limits
- Greedy AI opponent with scoring heuristics
- Floating damage / heal numbers with CSS animation
- Colour-coded combat log
- Weapon durability, Armor, Fatigue damage
- Board-aware targeting (buff spells highlight friendly minions; damage spells highlight enemies)

## Card Reference

| Card | Cost | Type | Effect |
|---|---|---|---|
| Peasant | 1 | Minion | 2/1 |
| Guard | 2 | Minion | 2/3 Taunt |
| Spider | 2 | Minion | 1/2 Poisonous |
| Cleric | 2 | Minion | 2/2 — Battlecry: Heal hero 3 |
| Bomber | 2 | Minion | 1/1 — Deathrattle: Deal 2 to enemy hero |
| Blessing | 2 | Spell | Give a friendly minion +2/+2 |
| Zap | 2 | Spell | Deal 3 damage |
| Raider | 3 | Minion | 4/2 |
| Knight | 3 | Minion | 3/1 Charge |
| Mend | 3 | Spell | Restore 5 HP |
| Insight | 3 | Spell | Draw 2 cards |
| Axe | 3 | Weapon | 3 Atk / 2 Durability |
| Paladin | 4 | Minion | 3/3 Taunt + Divine Shield |
| Blast | 4 | Spell | Deal 6 damage |
| Cleave | 4 | Spell | Deal 2 damage to all enemy minions |
| Dragon | 5 | Minion | 5/6 |

## Project Structure

```
LitStone/
├── game_logic.py       # Pure Python game engine (no GUI deps)
├── server.py           # Flask REST API
├── requirements.txt
├── templates/
│   └── index.html      # Single-page app (hero select → deck builder → game)
└── static/
    ├── style.css       # Full CSS design system
    └── game.js         # All frontend logic, API calls, selection state
```

## API

| Endpoint | Method | Description |
|---|---|---|
| `/api/cards` | GET | Card database and hero list |
| `/api/new_game` | POST `{hero_class, deck[]}` | Start a new game, returns state |
| `/api/action` | POST `{action, idx, target}` | Execute a move; AI responds; returns updated state |
| `/api/state` | GET | Current game state |
| `/api/legal_moves` | GET | List of valid moves for current player |

## Roadmap

See **[ROADMAP.md](ROADMAP.md)** for the full vision — three public-domain themed decks (Fantasy, Romantic, Monster), improved card art, LAN multiplayer, and more.

## License

MIT — see [LICENSE](LICENSE).
All card themes and characters are drawn from works in the **public domain**.
