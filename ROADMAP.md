# LitStone — Roadmap

This document tracks planned improvements and future directions for LitStone.

For the strategic plan to reach **Hearthstone Lite** quality, see [HEARTHSTONE_LITE_PLAN.md](HEARTHSTONE_LITE_PLAN.md).

---

## Version 0.x — Current (Foundation)

The current state of the project establishes the core gameplay loop.

- [x] Literary-themed card library (109 collectable cards + The Coin)
- [x] 6 hero classes with unique hero powers (Mage, Warrior, Priest, Rogue, Paladin, Shaman)
- [x] Full keyword system: Taunt, Divine Shield, Charge, Poisonous, Battlecry, Deathrattle, Silence
- [x] Deck builder (30 cards, max 2 copies; legendaries max 1)
- [x] Heuristic AI opponent
- [x] Flask REST API backend
- [x] Browser-based UI with combat log
- [x] Procedural card art — layered frames, class palettes, tooltip art previews
- [x] Title hub, settings modal, in-game pause, and match loading overlay
- [x] Deck builder — starter deck, mana cost filter, validation hints, continue last deck
- [x] Game speed settings (Normal / Fast / Instant) and lean match API payloads
- [x] Fatigue damage system
- [x] Weapon system
- [x] Mulligan phase (player)
- [x] Deck filter/sort, mana curve, save/load decks (localStorage)
- [x] Legendary minions (37 literary legends)
- [x] Unit tests — 146 tests covering game logic, AI, campaign API, and edge cases (`test_game_logic.py`)

---

## Version 1.0 — Stability & Polish

Goals: make the game feel complete and production-ready for single-player use.

- [x] **Persistent game state** — SQLite-backed game sessions survive server restarts
- [x] **Per-session game IDs** — UUID-keyed game sessions (`GAMES` dict)
- [x] **AI mulligan** — heuristic opening-hand swaps for the AI opponent
- [x] **Improved AI** — difficulty tiers (Easy/Normal/Hard), curved AI decks, boss opponents
- [x] **Partial card animations** — summon flash, damage float, buff glow, turn banner, hero flash
- [x] **Full card animations** — play-from-hand arc, attack lunge, death burst, weapon swing, spell flash
- [x] **Sound effects** — Web Audio SFX for play, attack, damage, heal, turn, victory/defeat (mute toggle)
- [x] **Partial responsive layout** — breakpoints at 900px / 1100px; mobile scroll fixes
- [x] **Partial mobile polish** — sticky hand/tray, collapsible log, touch targets, board scroll
- [x] **Partial mobile polish (≤375px)** — deck-builder and in-game controls meet 44px tap targets
- [x] **Error handling** — status toasts, illegal-move feedback, network error messages
- [x] **Resign cleanup** — `POST /api/resign` clears server state when leaving a match
- [x] **Unit tests** — comprehensive suite in `test_game_logic.py`

---

## Version 1.1 — Content Expansion

Goals: deepen the card pool and hero variety.

- [x] **More cards** — 109-card library (61 neutral + 48 class-exclusive)
- [x] **Additional hero classes** — Rogue, Paladin, and Shaman (Totemic Call)
- [x] **Class-specific cards** — 8 cards per class; neutrals usable by all heroes
- [x] **Legendary minions** — 37 high-impact unique cards (one copy per deck)
- [x] **30-card decks** — standard CCG deck size
- [x] **The Coin** — second-player gains +1 mana crystal (once)
- [x] **First-player randomization** — coin flip for who goes first
- [x] **Adventure / campaign mode** — 5-node campaign with 2 boss encounters and progress tracking

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

- [x] AI difficulty settings (Easy / Normal / Hard)
- [x] Tutorial match with in-game step hints
- [x] Practice sandbox mode (custom HP / infinite mana)
- Replay system — save and replay past games
- Draft / Arena mode — pick cards one at a time from random sets
- New keywords: Windfury, Lifesteal, Discover, Secrets
- Accessibility improvements (screen reader support, high-contrast theme)
- Localization (i18n framework for non-English languages)
