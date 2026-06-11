# LitStone — Roadmap

This document tracks planned improvements and future directions for LitStone.

For the strategic plan to reach **Hearthstone Lite** quality, see [HEARTHSTONE_LITE_PLAN.md](HEARTHSTONE_LITE_PLAN.md).

---

## Version 0.x — Current (Foundation)

The current state of the project establishes the core gameplay loop.

- [x] Literary-themed card library (61 cards: minions, spells, weapon, support spells)
- [x] 5 hero classes with unique hero powers (Mage, Warrior, Priest, Rogue, Paladin)
- [x] Full keyword system: Taunt, Divine Shield, Charge, Poisonous, Battlecry, Deathrattle, Silence
- [x] Deck builder (15 cards, max 2 copies; legendaries max 1)
- [x] Heuristic AI opponent
- [x] Flask REST API backend
- [x] Browser-based UI with combat log
- [x] Fatigue damage system
- [x] Weapon system
- [x] Mulligan phase (player)
- [x] Deck filter/sort, mana curve, save/load decks (localStorage)
- [x] Legendary minions (37 literary legends)
- [x] Unit tests — 113 tests covering game logic, AI, and edge cases (`test_game_logic.py`)

---

## Version 1.0 — Stability & Polish

Goals: make the game feel complete and production-ready for single-player use.

- [ ] **Persistent game state** — survive server restarts using a lightweight store (e.g. SQLite or JSON file)
- [ ] **Per-session game IDs** — support multiple concurrent games (replace global `GAME_STATE`)
- [ ] **Improved AI** — smarter target selection, mulligan, difficulty tiers, reduced random noise
- [x] **Partial card animations** — summon flash, damage float, buff glow, turn banner, hero flash
- [ ] **Full card animations** — play-from-hand arc, attack lunge, death removal
- [ ] **Sound effects** — basic audio feedback for card play, attacks, and victory
- [x] **Partial responsive layout** — breakpoints at 900px / 1100px; mobile scroll fixes
- [ ] **Full mobile polish** — playable board and hand on phone-sized viewports
- [x] **Error handling** — status toasts, illegal-move feedback, network error messages
- [x] **Resign cleanup** — `POST /api/resign` clears server state when leaving a match
- [x] **Unit tests** — comprehensive suite in `test_game_logic.py`

---

## Version 1.1 — Content Expansion

Goals: deepen the card pool and hero variety.

- [x] **More cards** — 61-card library with broad literary themes
- [x] **Additional hero classes** — Rogue and Paladin added; Shaman remains planned
- [ ] **Class-specific cards** — some cards restricted to certain hero classes
- [x] **Legendary minions** — 37 high-impact unique cards (one copy per deck)
- [ ] **30-card decks** — standard CCG deck size (see Hearthstone Lite plan)
- [ ] **The Coin** — second-player compensation
- [ ] **Adventure / campaign mode** — scripted encounters against bosses with predefined decks

---

## Version 1.2 — Multiplayer

Goals: allow two human players to compete.

- [ ] **Lobby system** — create and join game rooms via a short code or URL
- [ ] **WebSocket support** — real-time state sync using Flask-SocketIO or similar
- [ ] **Reconnect logic** — resume a game after connection loss
- [ ] **Spectator mode** — watch a game in progress without participating

---

## Version 2.0 — Accounts & Progression

Goals: give players a reason to keep coming back.

- [ ] **User accounts** — register, log in, save decks
- [ ] **Win/loss history** — per-account match record
- [ ] **Collection system** — players start with a base set and unlock cards through play
- [ ] **Daily quests** — earn rewards for completing in-game challenges
- [ ] **Leaderboard** — ranked mode with rating and seasonal resets

---

## Ongoing / Unscheduled

Ideas that may be incorporated into any version:

- AI difficulty settings (Easy / Normal / Hard)
- Replay system — save and replay past games
- Draft / Arena mode — pick cards one at a time from random sets
- New keywords: Windfury, Lifesteal, Discover, Secrets
- Accessibility improvements (screen reader support, high-contrast theme)
- Localization (i18n framework for non-English languages)
