# LitStone — Roadmap

This document tracks planned improvements and future directions for LitStone.

---

## Version 0.x — Current (Foundation)

The current state of the project establishes the core gameplay loop.

- [x] 16-card library (minions, spells, weapon)
- [x] 3 hero classes with unique hero powers (Mage, Warrior, Priest)
- [x] Full keyword system: Taunt, Divine Shield, Charge, Poisonous, Battlecry, Deathrattle
- [x] Deck builder (15 cards, max 2 copies)
- [x] Heuristic AI opponent
- [x] Flask REST API backend
- [x] Browser-based UI with combat log
- [x] Fatigue damage system
- [x] Weapon system

---

## Version 1.0 — Stability & Polish

Goals: make the game feel complete and production-ready for single-player use.

- [ ] **Persistent game state** — survive server restarts using a lightweight store (e.g. SQLite or JSON file)
- [ ] **Improved AI** — smarter target selection, better end-game recognition, and reduced random noise
- [ ] **Card animations** — play/attack/death animations in the frontend
- [ ] **Sound effects** — basic audio feedback for card play, attacks, and victory
- [ ] **Responsive layout** — mobile-friendly board and hand scaling
- [ ] **Error handling** — graceful UI feedback on illegal moves or server errors
- [ ] **Unit tests** — pytest suite covering game logic, AI moves, and edge cases

---

## Version 1.1 — Content Expansion

Goals: deepen the card pool and hero variety.

- [ ] **More cards** — expand the library to 30+ cards, including new spell types and minion keywords
- [ ] **Additional hero classes** — Rogue (poisoned blade), Paladin (divine inspiration), Shaman (totems)
- [ ] **Class-specific cards** — some cards restricted to certain hero classes
- [ ] **Legendary minions** — high-cost, high-impact unique cards (one copy per deck)
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
- Deck import/export via a compact string format
- Accessibility improvements (screen reader support, high-contrast theme)
- Localization (i18n framework for non-English languages)
