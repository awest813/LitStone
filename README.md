# LitStone

A lightweight, browser-based card game inspired by Hearthstone. Play against an AI opponent in a turn-based battle using minions, spells, and weapons.

## Features

- **4 Hero Classes** — Mage, Warrior, Priest, and Rogue, each with a unique hero power
- **56-card library** — Literary-themed minions, spells, and a weapon with distinct mechanics, plus 34 Legendary storybook heroes and villains
- **Rich card mechanics** — Taunt, Divine Shield, Charge, Poisonous, Battlecry, Deathrattle
- **Mulligan phase** — Select any opening-hand cards to redraw before each game starts
- **Literary Legends** — Legendary minions inspired by Sherlock Holmes, Dr. John Watson, Professor Moriarty, Van Helsing, Victor Frankenstein, Frankenstein's Monster, Alice, The Mad Hatter, The White Rabbit, The Queen of Hearts, The Cheshire Cat, Snow White, Rapunzel, Sleeping Beauty, Little Red Riding Hood, Rumpelstiltskin, The Big Bad Wolf, Pied Piper, Baba Yaga, Bluebeard, King Arthur, Merlin, Lancelot, Guinevere, Morgan le Fay, Mordred, Gawain, Robin Hood, Maid Marian, Friar Tuck, Little John, Will Scarlet, Ebenezer Scrooge, and Oliver Twist (max 1 copy per deck)
- **Deck Builder** — Build a custom 15-card deck (max 2 copies per card; max 1 copy of Legendary cards) before each game
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
| Rogue   | Dagger Mastery | Equip a 1/2 Wicked Dagger         |

### Card Types

| Type   | Description |
|--------|-------------|
| Minion | Placed on the board to attack and defend |
| Spell  | One-time effect (damage, heal, draw, AoE, buff) |
| Weapon | Equips to your hero, enabling direct attacks |

### Literary Legend Cards (Legendary — max 1 per deck)

These legendary minions are based on classic literature and folklore and have a distinctive golden card frame.

| Card | Cost | ATK | HP | Keywords / Ability | Source |
|------|------|-----|----|--------------------|--------|
| Sherlock Holmes | 5 | 2 | 6 | Battlecry: draw 2 cards | *Sherlock Holmes* (Doyle) |
| Dr. John Watson | 4 | 3 | 5 | Battlecry: heal hero 4 | *Sherlock Holmes* (Doyle) |
| Professor Moriarty | 6 | 5 | 5 | Poisonous · Deathrattle: deal 3 dmg | *Sherlock Holmes* (Doyle) |
| Van Helsing | 5 | 5 | 4 | Charge | *Dracula* (Stoker) |
| Victor Frankenstein | 4 | 3 | 6 | Battlecry: draw 1 card | *Frankenstein* (Shelley) |
| Frankenstein's Monster | 6 | 6 | 6 | Taunt · Deathrattle: deal 3 dmg | *Frankenstein* (Shelley) |
| Alice | 3 | 3 | 4 | Battlecry: draw 1 card | *Alice's Adventures in Wonderland* (Carroll) |
| The Mad Hatter | 6 | 4 | 5 | Battlecry: draw 2 cards | *Alice's Adventures in Wonderland* (Carroll) |
| The White Rabbit | 3 | 2 | 3 | Charge | *Alice's Adventures in Wonderland* (Carroll) |
| The Queen of Hearts | 6 | 6 | 5 | Taunt | *Alice's Adventures in Wonderland* (Carroll) |
| The Cheshire Cat | 4 | 4 | 4 | Divine Shield | *Alice's Adventures in Wonderland* (Carroll) |
| Snow White | 5 | 3 | 7 | Divine Shield | *Snow White* (Grimm) |
| Rapunzel | 4 | 2 | 6 | Battlecry: heal hero 3 | *Rapunzel* (Grimm) |
| Sleeping Beauty | 3 | 2 | 5 | Divine Shield | *Sleeping Beauty* (Perrault/Grimm) |
| Little Red Riding Hood | 4 | 4 | 3 | Charge | *Little Red Riding Hood* (Perrault/Grimm) |
| Rumpelstiltskin | 5 | 4 | 4 | Deathrattle: deal 3 dmg | *Rumpelstiltskin* (Grimm) |
| The Big Bad Wolf | 5 | 5 | 3 | Charge | *Little Red Riding Hood* (Perrault/Grimm) |
| Pied Piper | 4 | 3 | 5 | Battlecry: draw 1 card | *The Pied Piper of Hamelin* (Browning/Grimm) |
| Baba Yaga | 6 | 5 | 5 | Poisonous | Slavic folklore |
| Bluebeard | 5 | 5 | 4 | Taunt | *Bluebeard* (Perrault) |
| King Arthur | 7 | 6 | 8 | Taunt | Arthurian legend |
| Merlin | 6 | 4 | 7 | Battlecry: draw 2 cards | Arthurian legend |
| Lancelot | 5 | 5 | 3 | Charge | Arthurian legend |
| Guinevere | 4 | 3 | 6 | Divine Shield | Arthurian legend |
| Morgan le Fay | 6 | 5 | 5 | Poisonous | Arthurian legend |
| Mordred | 6 | 6 | 4 | Deathrattle: deal 3 dmg | Arthurian legend |
| Gawain | 5 | 4 | 6 | Taunt | Arthurian legend |
| Robin Hood | 4 | 4 | 3 | Charge | English folklore |
| Maid Marian | 3 | 3 | 4 | Battlecry: heal hero 3 | English folklore |
| Friar Tuck | 4 | 3 | 6 | Taunt | English folklore |
| Little John | 4 | 4 | 5 | Taunt | English folklore |
| Will Scarlet | 3 | 3 | 2 | Charge | English folklore |
| Ebenezer Scrooge | 5 | 3 | 7 | Battlecry: draw 2 cards | *A Christmas Carol* (Dickens) |
| Oliver Twist | 3 | 3 | 3 | Battlecry: draw 1 card | *Oliver Twist* (Dickens) |

### Literary Support Spells

| Card | Cost | Effect |
|------|------|--------|
| Library Whisper | 1 | Draw 1 card |
| Nevermore | 3 | Deal 4 damage |
| Elixir of Life | 2 | Restore 4 HP |
| Rallying Banner | 3 | Give all friendly minions +1/+1 |
| Circle of Mending | 3 | Restore 3 HP to all friendly characters |
| Enchanted Shield | 2 | Give a friendly minion Divine Shield |

### Core Set Minions & Spells

- Minions: Town Crier, Castle Guard, Highwayman, Errant Knight, Templar Captain, Storybook Dragon, Cave Spider, Cathedral Cleric, Tinker Alchemist.
- Spells & weapon: Quill Bolt, Inferno Verse, Restorative Hymn, Deductive Clue, Rebel's Ambush, Fairy Blessing, Heroic Blade.

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
