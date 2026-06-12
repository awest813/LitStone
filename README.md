# LitStone

A lightweight, browser-based card game inspired by Hearthstone. Play against an AI opponent in a turn-based battle using minions, spells, and weapons.

**Roadmap:** [ROADMAP.md](ROADMAP.md) · **Hearthstone Lite plan:** [HEARTHSTONE_LITE_PLAN.md](HEARTHSTONE_LITE_PLAN.md)

## Features

- **6 Hero Classes** — Mage, Warrior, Priest, Rogue, Paladin, and Shaman, each with a unique hero power
- **109-card library** — Neutral literary cards plus 8 class-exclusive cards per hero (48 class cards), including 37 Legendary minions
- **Rich card mechanics** — Taunt, Divine Shield, Charge, Poisonous, Battlecry, Deathrattle, Silence
- **Mulligan phase** — Select any opening-hand cards to redraw before each game starts
- **Literary Legends** — Legendary minions inspired by Sherlock Holmes, Dr. John Watson, Professor Moriarty, Van Helsing, Victor Frankenstein, Frankenstein's Monster, Alice, The Mad Hatter, The White Rabbit, The Queen of Hearts, The Cheshire Cat, Snow White, Rapunzel, Sleeping Beauty, Little Red Riding Hood, Rumpelstiltskin, The Big Bad Wolf, Pied Piper, Baba Yaga, Bluebeard, King Arthur, Merlin, Lancelot, Guinevere, Morgan le Fay, Mordred, Gawain, Robin Hood, Maid Marian, Friar Tuck, Little John, Will Scarlet, Ebenezer Scrooge, Oliver Twist, Ivanhoe, Quasimodo, and Don Quixote (max 1 copy per deck)
- **Deck Builder** — Build a custom 30-card deck (max 2 copies per card; max 1 copy of Legendary cards) before each game
- **AI opponent** — Heuristic-driven AI with Easy / Normal / Hard difficulty and curved decks
- **Career & tutorial** — 6-chapter Literary Career (3 boss duels: Frankenstein, Van Helsing, Moriarty), guided tutorial, and practice sandbox
- **Session persistence** — active games saved to SQLite and restored after server restart
- **Combat log** — Real-time log of every action taken during the game
- **Fatigue system** — Players take increasing damage when their deck runs out

## Tech Stack

| Layer    | Technology |
|----------|------------|
| Backend  | Python 3.12 + Flask |
| Production | Gunicorn + WhiteNoise |
| Frontend | Vanilla JavaScript, HTML5, CSS3 |
| Frontend libs | [fuzzysort](https://github.com/farzher/fuzzysort) (MIT), [NProgress](https://github.com/rstacruz/nprogress) (MIT) |
| Fonts    | Google Fonts (Cinzel, Crimson Text) |
| CI       | GitHub Actions (pytest + Ruff) |

## Getting Started

### Prerequisites

- Python 3.12+ (matches CI)
- pip

### Installation

```bash
git clone https://github.com/awest813/LitStone.git
cd LitStone
pip install -r requirements-dev.txt
```

### Running the server

Development:

```bash
python3 server.py
```

Production (Gunicorn):

```bash
gunicorn -c gunicorn.conf.py wsgi:app
```

Docker:

```bash
docker build -t litstone .
docker run -p 5000:5000 litstone
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

Run tests and lint:

```bash
pytest test_game_logic.py test_career_playthrough.py test_career_browser.py -q
playwright install chromium   # once, for browser E2E
ruff check .
```

The suite has **193** tests (game logic, career API, and Playwright browser E2E).

Third-party licenses: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)

## How to Play

1. From the **title hub**, pick **Play**, **Career**, **Practice**, or **Tutorial**.
2. **Choose a hero class**, then **build a 30-card deck** (up to 2 copies each; legendaries max 1).
3. **Mulligan** any opening-hand cards you want to replace, then confirm.
4. On your turn, play cards, attack with minions or your hero, and use your hero power.
5. Click **End Turn** to let the AI take its turn.
6. Reduce the opponent's hero HP to 0 to win.

**Practice sandbox:** set custom hero HP and optional infinite mana before building your deck.

### Hero Powers (cost 2 mana, once per turn)

| Hero    | Power        | Effect                              |
|---------|--------------|-------------------------------------|
| Mage    | Fireblast    | Deal 1 damage to any target         |
| Warrior | Armor Up!    | Gain 2 Armor                        |
| Priest  | Lesser Heal  | Restore 2 HP to a friendly character |
| Rogue   | Dagger Mastery | Equip a 1/2 Wicked Dagger         |
| Paladin | Reinforce      | Summon a 1/1 Silver Hand Recruit   |
| Shaman  | Totemic Call   | Summon a random Totem              |

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
| Little Red Riding Hood | 4 | 3 | 5 | Charge | *Little Red Riding Hood* (Perrault/Grimm) |
| Rumpelstiltskin | 5 | 4 | 4 | Deathrattle: deal 3 dmg | *Rumpelstiltskin* (Grimm) |
| The Big Bad Wolf | 5 | 5 | 2 | Charge · Poisonous | *Little Red Riding Hood* (Perrault/Grimm) |
| Pied Piper | 4 | 3 | 5 | Battlecry: draw 1 card | *The Pied Piper of Hamelin* (Browning/Grimm) |
| Baba Yaga | 6 | 5 | 5 | Poisonous | Slavic folklore |
| Bluebeard | 5 | 5 | 4 | Taunt | *Bluebeard* (Perrault) |
| King Arthur | 7 | 6 | 8 | Taunt | Arthurian legend |
| Merlin | 6 | 4 | 7 | Battlecry: heal hero 6 | Arthurian legend |
| Lancelot | 5 | 5 | 3 | Charge | Arthurian legend |
| Guinevere | 4 | 3 | 6 | Divine Shield | Arthurian legend |
| Morgan le Fay | 6 | 5 | 6 | Divine Shield | Arthurian legend |
| Mordred | 6 | 6 | 4 | Deathrattle: deal 3 dmg | Arthurian legend |
| Gawain | 5 | 4 | 6 | Taunt | Arthurian legend |
| Robin Hood | 4 | 4 | 3 | Charge | English folklore |
| Maid Marian | 3 | 3 | 4 | Battlecry: heal hero 3 | English folklore |
| Friar Tuck | 4 | 3 | 6 | Taunt | English folklore |
| Little John | 4 | 4 | 5 | Taunt | English folklore |
| Will Scarlet | 3 | 3 | 2 | Charge | English folklore |
| Ebenezer Scrooge | 5 | 3 | 7 | Battlecry: draw 2 cards | *A Christmas Carol* (Dickens) |
| Oliver Twist | 3 | 3 | 3 | Battlecry: draw 1 card | *Oliver Twist* (Dickens) |
| Ivanhoe | 5 | 4 | 5 | Taunt · Divine Shield | *Ivanhoe* (Scott) |
| Quasimodo | 4 | 2 | 7 | Taunt · Battlecry: heal hero 2 | *The Hunchback of Notre-Dame* (Hugo) |
| Don Quixote | 3 | 4 | 2 | Charge | *Don Quixote* (Cervantes) |

### Literary Support Spells

| Card | Cost | Effect |
|------|------|--------|
| Library Whisper | 1 | Draw 1 card |
| Nevermore | 3 | Deal 4 damage |
| Elixir of Life | 2 | Restore 4 HP |
| Rallying Banner | 3 | Give all friendly minions +1/+1 |
| Circle of Mending | 3 | Restore 3 HP to all friendly characters |
| Enchanted Shield | 1 | Give a friendly minion Divine Shield |
| Inkwell Blast | 2 | Deal 1 damage to all enemy minions |
| Tome of Silence | 3 | Remove all text from an enemy minion |

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
| Silence       | Removes all keywords and text from a minion |

## Project Structure

```
LitStone/
├── game_logic.py        # Pure Python game rules, AI, and card database
├── game_store.py        # SQLite persistence for active sessions
├── server.py            # Flask server and REST API
├── career_test_support.py  # Shared helpers for career E2E tests
├── conftest.py          # Pytest fixtures (live server, Playwright browser)
├── test_game_logic.py   # Unit tests (game logic + API)
├── test_career_playthrough.py  # End-to-end career flow via API
├── test_career_browser.py      # Playwright browser E2E for career UI
├── requirements.txt     # Python runtime dependencies
├── requirements-dev.txt # pytest, Ruff, and runtime deps
├── THIRD_PARTY_NOTICES.md  # MIT and other OSS attributions
├── Dockerfile           # Production container (gunicorn)
├── wsgi.py              # WSGI entry for gunicorn
├── ROADMAP.md           # Version roadmap
├── HEARTHSTONE_LITE_PLAN.md  # Strategic plan for HS-lite quality
├── templates/
│   └── index.html       # Single-page HTML shell
└── static/
    ├── game.js          # All frontend game logic and rendering
    ├── card-art.js      # Procedural card art rendering
    ├── style.css        # Core styling and animations
    ├── screens.css      # Hub, modals, campaign, practice screens
    ├── card-frames.css  # Card frame styles
    └── vendor/          # Vendored MIT JS (fuzzysort, NProgress)
```

## API Endpoints

| Method | Route              | Description                      |
|--------|--------------------|----------------------------------|
| GET    | `/`                | Serves the game UI               |
| GET    | `/api/health`      | Server health check              |
| GET    | `/api/campaign`    | Career chapter list with opponent metadata |
| GET    | `/api/starter_deck`| Curved 30-card starter list for a hero class |
| GET    | `/api/cards`       | Returns the full card database   |
| POST   | `/api/new_game`    | Starts a new game session        |
| POST   | `/api/mulligan`    | Submit mulligan card swaps       |
| GET    | `/api/state`       | Returns the current game state   |
| POST   | `/api/action`      | Executes a player action         |
| POST   | `/api/resign`      | Abandon the current game         |
| GET    | `/api/legal_moves` | Returns all legal moves for P1   |

## License

See [LICENSE](LICENSE).
