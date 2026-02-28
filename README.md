# LitStone

A lightweight, browser-based card game inspired by Hearthstone. Play against an AI opponent in a turn-based battle using minions, spells, and weapons.

## Features

- **3 Hero Classes** — Mage, Warrior, and Priest, each with a unique hero power
- **16-card library** — Minions, spells, and weapons with distinct mechanics
- **Rich card mechanics** — Taunt, Divine Shield, Charge, Poisonous, Battlecry, Deathrattle
- **Deck Builder** — Build a custom 15-card deck (max 2 copies per card) before each game
- **AI opponent** — Heuristic-driven AI that evaluates board state and plays competitively
- **Combat log** — Real-time log of every action taken during the game
- **Fatigue system** — Players take increasing damage when their deck runs out

## Tech Stack

| Layer    | Technology |
|----------|------------|
| Backend  | Python 3.12 + Flask |
| Frontend | Vanilla JavaScript, HTML5, CSS3 |
| Fonts    | Google Fonts (Cinzel, Crimson Text) |

## Getting Started

### Prerequisites

- Python 3.10+
- pip

### Installation

```bash
git clone https://github.com/awest813/LitStone.git
cd LitStone
pip install -r requirements.txt
```

### Running the server

```bash
python server.py
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

## How to Play

1. **Choose a Hero Class** on the main menu.
2. **Build your deck** — select 15 cards from the card pool (up to 2 copies each).
3. Click **Play vs AI** to start the game.
4. On your turn, play cards from your hand, attack with minions or your hero, and use your hero power.
5. Click **End Turn** to let the AI take its turn.
6. Reduce the opponent's hero HP to 0 to win.

### Hero Powers (cost 2 mana, once per turn)

| Hero    | Power        | Effect                              |
|---------|--------------|-------------------------------------|
| Mage    | Fireblast    | Deal 1 damage to any target         |
| Warrior | Armor Up!    | Gain 2 Armor                        |
| Priest  | Lesser Heal  | Restore 2 HP to a friendly character |

### Card Types

| Type   | Description |
|--------|-------------|
| Minion | Placed on the board to attack and defend |
| Spell  | One-time effect (damage, heal, draw, AoE, buff) |
| Weapon | Equips to your hero, enabling direct attacks |

### Keyword Reference

| Keyword       | Effect |
|---------------|--------|
| Taunt         | Enemies must attack this minion first |
| Divine Shield | Absorbs the first instance of damage |
| Charge        | Can attack the same turn it is played |
| Poisonous     | Destroys any minion it damages |
| Battlecry     | Triggers an effect when played from hand |
| Deathrattle   | Triggers an effect when the minion dies |

## Project Structure

```
LitStone/
├── game_logic.py        # Pure Python game rules, AI, and card database
├── server.py            # Flask server and REST API
├── requirements.txt     # Python dependencies
├── templates/
│   └── index.html       # Single-page HTML shell
└── static/
    ├── game.js          # All frontend game logic and rendering
    └── style.css        # Styling and animations
```

## API Endpoints

| Method | Route              | Description                      |
|--------|--------------------|----------------------------------|
| GET    | `/`                | Serves the game UI               |
| GET    | `/api/cards`       | Returns the full card database   |
| POST   | `/api/new_game`    | Starts a new game session        |
| GET    | `/api/state`       | Returns the current game state   |
| POST   | `/api/action`      | Executes a player action         |
| GET    | `/api/legal_moves` | Returns all legal moves for P1   |

## License

See [LICENSE](LICENSE).
