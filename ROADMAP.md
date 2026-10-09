# LitStone — Roadmap

This document tracks planned improvements and future directions for LitStone.

For the strategic plan to reach **Hearthstone Lite** quality, see [HEARTHSTONE_LITE_PLAN.md](HEARTHSTONE_LITE_PLAN.md).

---

## Version 0.x — Current (Foundation)

The current state of the project establishes the core gameplay loop.

- [x] Literary-themed card library (117 collectable cards + The Coin)
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
- [x] Unit tests — 236 tests covering game logic, AI, career API, and browser E2E (`test_game_logic.py`, `test_career_playthrough.py`, `test_career_browser.py`)

---

## Version 1.0 — Stability & Polish

Goals: make the game feel complete and production-ready for single-player use.

- [x] **Persistent game state** — SQLite-backed game sessions survive server restarts
- [x] **Per-session game IDs** — UUID-keyed game sessions (`GAMES` dict)
- [x] **AI mulligan** — heuristic opening-hand swaps for the AI opponent
- [x] **Improved AI** — difficulty tiers (Easy/Normal/Hard), curved AI decks, boss opponents
- [x] **AI Personalities & Combined Lethal Solver** — 7 playstyles (Midrange, Ramp, Control, Aggro, Gambler, Value, Balanced), multi-action lethal calculation, overdraw prevention, weapon self-preservation
- [x] **AI Personalities UI Exposure** — Practice Sandbox and Deck Builder match options allow players to select opponent playstyle archetype directly
- [x] **Title Hub & Screen Polish** — balanced responsive mode grid with tutorial banner, widened practice panel, and deck builder match controls
- [x] **Card Balance Optimization** — 100-run simulation benchmark audit resulting in nerfs to overtuned cards (`Shieldwall Sergeant`, `Lancelot`, `Alice`) and buffs to trap cards (`Shiv Storm`, `Cleave Chronicle`, `Thief's Shiv`, `Hex of Baba`)
- [x] **Campaign Boss Tuning** — rebalanced `Van Helsing` and `Professor Moriarty`, with thematic AI personalities per chapter
- [x] **Partial card animations** — summon flash, damage float, buff glow, turn banner, hero flash
- [x] **Full card animations** — play-from-hand arc, attack lunge, death burst, weapon swing, spell flash
- [x] **Arched Combat Targeting Arrow** — dynamic quadratic bezier vector arc with energy dash flow, arrowhead tracking, target snapping, and rotating target reticle
- [x] **Tactile Screen Rumble & Combat FX** — screen/board camera shake scaling with impact severity (light, medium, heavy), slash marks, and deep sub-bass crunch
- [x] **Hero Emotes & Speech Bubbles** — 6-way emote wheel (Greetings, Well Played, Thanks, Wow, Oops, Threaten) with class-specific literary dialogue, parchment bubbles, and AI retorts
- [x] **3D Card Hover Depth & Holographic Sheen** — dynamic 3D cursor-tracking perspective tilt on hand cards and animated prismatic holofoil reflection on hand cards and collection pool cards
- [x] **Sound effects** — Web Audio SFX for play, attack, damage, heal, turn, victory/defeat, coin flip, heavy hits, emotes (mute toggle)
- [x] **Partial responsive layout** — breakpoints at 900px / 1100px; mobile scroll fixes
- [x] **Partial mobile polish** — sticky hand/tray, collapsible log, touch targets, board scroll
- [x] **Partial mobile polish (≤375px)** — deck-builder and in-game controls meet 44px tap targets
- [x] **Error handling** — status toasts, illegal-move feedback, network error messages
- [x] **Resign cleanup** — `POST /api/resign` clears server state when leaving a match
- [x] **Unit tests** — comprehensive suite in `test_game_logic.py`

---

## Version 1.1 — Content Expansion

Goals: deepen the card pool and hero variety.

- [x] **More cards** — 117-card library (69 neutral + 48 class-exclusive)
- [x] **Additional hero classes** — Rogue, Paladin, and Shaman (Totemic Call)
- [x] **Class-specific cards** — 8 cards per class; neutrals usable by all heroes
- [x] **Legendary minions** — 37 high-impact unique cards (one copy per deck)
- [x] **30-card decks** — standard CCG deck size
- [x] **The Coin** — second-player gains +1 mana crystal (once)
- [x] **First-player randomization** — coin flip for who goes first
- [x] **Literary Career mode** — 6-chapter career with 3 boss encounters (Frankenstein, Van Helsing, Moriarty) and progress tracking
- [x] **Premium Hero Graphics** — High-resolution fantasy digital art portraits for all 6 hero classes (Mage, Warrior, Priest, Rogue, Paladin, Shaman) integrated into Class Select cards, in-game hero trays, and deck builder emblem with sculpted golden bezels and class aura effects
- [x] **Literary Anthology & Lore System** — 100% lore coverage for all 110 cards plus hero power tokens (Silver Hand Recruit, Wicked Dagger, Searing/Healing/Stonefang/Wrath Totems) with authentic citations, authors, works, and publication dates
- [x] **Illuminated Card Inspect Modal** — two-column literary grimoire inspection modal with large card art, stats, rules text, battlecry quotes, and anthology citations (accessible via right-click or [I] key across pool, deck, hand, board, and hero trays)
- [x] **Chapter & Roman Turn Banners** — turn notifications rendered as dramatic book chapters (Prologue, Chapter I through X, The Climax)
- [x] **Dynamic Legendary Battlecry Speeches** — atmospheric speech bubbles quoting classic literature when legendary cards are summoned by player or AI
- [x] **Match Epilogues & Campaign Epigraphs** — thematic classical quotes concluding matches and introducing campaign chapters
- [x] **Windfury & Lifesteal** — minions may attack twice per turn or heal their hero from damage dealt
- [x] **Discover** — choose one of three offered cards to add to your hand (spell + UI modal + AI auto-pick)
- [x] **Secrets** — hidden reactive traps that trigger on an opponent's minion play, spell cast, or attack
- [x] **Mobile board readability** — larger minion slots and tap-to-preview cards on touch in duels
- [x] **Server-side deck storage** — account-less saved decks keyed by a browser token (`/api/decks`)
- [x] **Practice quick-start presets** — one-tap sandbox entry with a curved starter deck for any class, plus a no-AI solo toggle

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
- [x] Draft / Arena mode — pick 1 of 3 cards thirty times to build a deck, then duel
- [x] New keywords: Windfury, Lifesteal, Discover, Secrets
- [x] Accessibility improvements — high-contrast theme toggle, strong focus rings, ARIA labels/roles
- Localization (i18n framework for non-English languages)
