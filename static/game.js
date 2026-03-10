/* ============================================================
   LitStone — Frontend Game Logic (game.js)
   All UI rendering, selection state, and server communication.
   ============================================================ */

"use strict";

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------
let CARD_DB   = {};          // injected on first server response
let gameState = null;        // latest server state snapshot
let selected  = null;        // { type: "hand"|"board"|"hero_power"|"hero_weapon", idx }
let draftDeck = [];
let selectedClass = null;

// UI state
let isActing          = false; // prevents double-submit during server round-trips
let prevIsPlayerTurn  = null;  // tracks turn transitions for banner
let turnNumber        = 0;     // client-side turn counter

const KW_COLORS = {
  taunt: "#c0392b", divine_shield: "#d4a800", charge: "#00a878",
  poisonous: "#8e44ad", battlecry: "#2371b5", deathrattle: "#404e5c",
};
const KW_SHORT = [
  ["taunt","TAUNT"], ["divine_shield","SHIELD"], ["charge","CHARGE"],
  ["poisonous","POISON"], ["battlecry","B.CRY"], ["deathrattle","D.RATTLE"],
];
const CARD_EMOJIS = {
  PE:"🪚", GD:"🛡️", RD:"🪓", KN:"⚔️", PA:"🏰", DR:"🐉",
  SP:"🕷️", CL:"📖", BM:"💣", ZP:"⚡", BL:"💥", MD:"💚",
  IN:"🔍", CV:"🌊", BS:"✨", AX:"⚒️",
};

// Hero class accent colors
const HERO_COLORS = {
  Mage: "#2980b9", Warrior: "#c0392b", Priest: "#d4820a",
};

// ---------------------------------------------------------------------------
// Screen helpers
// ---------------------------------------------------------------------------
function showScreen(id) {
  document.querySelectorAll(".screen").forEach(s => {
    s.classList.toggle("active", s.id === id);
    s.style.display = s.id === id ? "" : "none";
  });
  if (id === "screen-game") {
    document.getElementById("screen-game").style.display = "grid";
  }
}

// ---------------------------------------------------------------------------
// MENU
// ---------------------------------------------------------------------------
function selectClass(cls) {
  selectedClass = cls;
  draftDeck = [];
  showScreen("screen-deck");
  document.getElementById("deck-title").textContent = `Build Your ${cls} Deck`;
  renderCardPool();
  updateDeckSidebar();
}

// ---------------------------------------------------------------------------
// DECK BUILDER
// ---------------------------------------------------------------------------
function renderCardPool() {
  const pool = document.getElementById("card-pool");
  pool.innerHTML = "";

  Object.entries(CARD_DB).forEach(([name, card]) => {
    const count  = draftDeck.filter(c => c === name).length;
    const isFull = count >= 2 || draftDeck.length >= 15;
    const div    = document.createElement("div");
    div.className = `pool-card pool-card--${card.type}${isFull ? " pool-card--full" : ""}`;
    div.dataset.name = name;

    const icon = CARD_EMOJIS[card.icon] || card.icon;

    let statsHtml = "";
    if (card.type === "minion") {
      statsHtml = `<div class="pool-stats">
        <span class="stat-atk">${card.atk}⚔</span>
        <span class="stat-hp">${card.hp}♥</span>
      </div>`;
      const kws = KW_SHORT.filter(([k]) => card[k]).map(([k, l]) =>
        `<span class="kw-badge" style="background:${KW_COLORS[k]};color:#fff">${l}</span>`
      ).join("");
      if (kws) statsHtml += `<div class="kw-badges" style="margin-top:2px">${kws}</div>`;
    } else if (card.type === "weapon") {
      statsHtml = `<div class="pool-stats">
        <span class="stat-atk">${card.atk}⚔</span>
        <span class="stat-dur">${card.durability}🛡</span>
      </div>`;
    } else {
      statsHtml = `<div class="pool-desc">${spellDesc(card, true)}</div>`;
    }

    div.innerHTML = `
      <div class="gem-cost">${card.cost}</div>
      ${count > 0 ? `<div class="gem-count">${count}</div>` : ""}
      <div class="pool-art">${icon}</div>
      <div class="pool-name">${name}</div>
      ${statsHtml}
    `;
    if (!isFull) {
      div.addEventListener("click", () => addCardToDeck(name));
    }
    div.addEventListener("mouseenter", e => showPoolTooltip(e, name, card));
    div.addEventListener("mouseleave", () => hideTooltip("card-tooltip"));
    pool.appendChild(div);
  });
}

function addCardToDeck(name) {
  if (draftDeck.length >= 15) return;
  if (draftDeck.filter(c => c === name).length >= 2) return;
  draftDeck.push(name);
  renderCardPool();
  updateDeckSidebar();
}

function removeFromDeck(name) {
  const i = draftDeck.indexOf(name);
  if (i !== -1) draftDeck.splice(i, 1);
  renderCardPool();
  updateDeckSidebar();
}

function updateDeckSidebar() {
  const count  = draftDeck.length;
  document.getElementById("deck-count").textContent    = count;
  document.getElementById("deck-progress").style.width = `${(count / 15) * 100}%`;

  const list   = document.getElementById("deck-list");
  list.innerHTML = "";
  const unique = [...new Set(draftDeck)].sort();
  unique.forEach(name => {
    const n   = draftDeck.filter(c => c === name).length;
    const li  = document.createElement("li");
    li.className = "deck-entry";
    li.innerHTML = `<span class="deck-entry-name">${name}</span>
                    <span class="deck-entry-count">x${n}</span>
                    <span class="deck-entry-remove" title="Remove">✕</span>`;
    li.querySelector(".deck-entry-remove").addEventListener("click", () => removeFromDeck(name));
    list.appendChild(li);
  });

  document.getElementById("btn-start-ai").disabled = count !== 15;
}

async function startGame() {
  if (draftDeck.length !== 15) return;
  try {
    const res  = await fetch("/api/new_game", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ hero_class: selectedClass, deck: draftDeck }),
    });
    const data = await res.json();
    CARD_DB          = data.card_db;
    gameState        = data;
    selected         = null;
    prevIsPlayerTurn = null;
    turnNumber       = 1;
    isActing         = false;
    showScreen("screen-game");
    showTurnBanner(true);
    renderGame();
  } catch (err) {
    showStatusToast("Failed to start game. Check your connection and try again.");
  }
}

function goBack() {
  showScreen("screen-menu");
}

function showStatusToast(message, ms = 2400) {
  const toast = document.getElementById("status-toast");
  if (!toast) return;
  toast.textContent = message;
  toast.classList.remove("hidden");
  clearTimeout(showStatusToast._timer);
  showStatusToast._timer = setTimeout(() => toast.classList.add("hidden"), ms);
}

// ---------------------------------------------------------------------------
// TOOLTIP
// ---------------------------------------------------------------------------
function spellDesc(card, short = false) {
  const e = card.effect, v = card.val;
  if (e === "damage")     return short ? `Deal ${v} Dmg`       : `Deal ${v} damage.`;
  if (e === "heal")       return short ? `Heal ${v} HP`        : `Restore ${v} HP.`;
  if (e === "draw")       return short ? `Draw ${v} Cards`     : `Draw ${v} cards.`;
  if (e === "damage_all") return short ? `AoE ${v} Dmg`        : `Deal ${v} dmg to all enemy minions.`;
  if (e === "buff")       return short ? `Buff +${v[0]}/+${v[1]}` : `Give a minion +${v[0]}/+${v[1]}.`;
  return "";
}

function battlecryDesc(bc) {
  if (!bc) return "";
  if (bc.effect === "heal_hero") return `Battlecry: Restore ${bc.val} HP to your hero.`;
  return "";
}

function deathrattleDesc(dr) {
  if (!dr) return "";
  if (dr.effect === "dmg_hero") return `Deathrattle: Deal ${dr.val} damage to the enemy hero.`;
  return "";
}

function buildTooltipHtml(name, card) {
  const isMinion = card.type === "minion";
  const isWeapon = card.type === "weapon";
  const isSpell  = card.type === "spell";

  let stats = "";
  if (isMinion) stats = `<div class="tooltip-stats">ATK ${card.atk} &nbsp;·&nbsp; HP ${card.hp}</div>`;
  if (isWeapon) stats = `<div class="tooltip-stats">ATK ${card.atk} &nbsp;·&nbsp; Dur ${card.durability}</div>`;
  if (isSpell)  stats = `<div class="tooltip-desc">${spellDesc(card)}</div>`;

  const kws = KW_SHORT.filter(([k]) => card[k]).map(([k, l]) =>
    `<div class="tooltip-kw" style="color:${KW_COLORS[k]}">${l}</div>`
  ).join("");

  const bcText = battlecryDesc(card.battlecry);
  const drText = deathrattleDesc(card.deathrattle);
  const abilities = [bcText, drText].filter(Boolean).map(t =>
    `<div class="tooltip-desc" style="margin-top:4px">${t}</div>`
  ).join("");

  return `
    <div class="tooltip-name">${name}</div>
    <div class="tooltip-type">${card.type.toUpperCase()} · ${card.cost} Mana</div>
    ${stats}
    ${kws}
    ${abilities}
  `;
}

function positionTooltip(el, x, y) {
  const W = window.innerWidth, H = window.innerHeight;
  const TW = el.offsetWidth  || 190;
  const TH = el.offsetHeight || 200;
  let tx = x + 16, ty = y;
  if (tx + TW > W - 10) tx = x - TW - 10;
  if (ty + TH > H - 10) ty = H - TH - 10;
  el.style.left = tx + "px";
  el.style.top  = ty + "px";
}

function showPoolTooltip(e, name, card) {
  const tt = document.getElementById("card-tooltip");
  tt.innerHTML = buildTooltipHtml(name, card);
  tt.classList.remove("hidden");
  positionTooltip(tt, e.clientX, e.clientY);
}

function showGameTooltip(e, name, card) {
  const tt = document.getElementById("game-tooltip");
  tt.innerHTML = buildTooltipHtml(name, card);
  tt.classList.remove("hidden");
  positionTooltip(tt, e.clientX, e.clientY);
}

function hideTooltip(id) {
  document.getElementById(id)?.classList.add("hidden");
}

// ---------------------------------------------------------------------------
// TURN BANNER & AI INDICATOR
// ---------------------------------------------------------------------------

function showTurnBanner(isPlayerTurn) {
  const banner = document.getElementById("turn-banner");
  if (!banner) return;
  // Reset: remove active so re-triggering re-plays the animation
  banner.className = `turn-banner turn-banner--${isPlayerTurn ? "player" : "enemy"}`;
  banner.textContent = isPlayerTurn ? "YOUR TURN" : "ENEMY TURN";
  // Force reflow so animation restarts cleanly
  void banner.offsetWidth;
  banner.classList.add("active");
}

function setAiThinking(active) {
  const bar = document.getElementById("ai-thinking-bar");
  if (bar) bar.classList.toggle("active", active);
  const etBtn = document.getElementById("btn-end-turn");
  if (etBtn) etBtn.textContent = active ? "AI thinking…" : "End Turn";
}

// ---------------------------------------------------------------------------
// ANIMATION HELPERS
// ---------------------------------------------------------------------------

/** Snapshot both boards for diff-based animation */
function snapshotBoards() {
  if (!gameState) return null;
  return {
    p1: gameState.p1.board.map(m => ({ name: m.name, hp: m.hp, atk: m.atk })),
    p2: gameState.p2.board.map(m => ({ name: m.name, hp: m.hp, atk: m.atk })),
  };
}

/**
 * After rendering, apply animations by comparing old vs new board state.
 * Also spawns anchored floating numbers for damage, heals, and buffs.
 * @param {object} prev - snapshotBoards() result taken before the action
 */
function applyPostRenderAnimations(prev) {
  if (!prev || !gameState) return;

  const pairs = [
    { prev: prev.p1, curr: gameState.p1.board, elId: "board-player" },
    { prev: prev.p2, curr: gameState.p2.board, elId: "board-opp" },
  ];

  pairs.forEach(({ prev: prevBoard, curr: currBoard, elId }) => {
    const boardEl = document.getElementById(elId);
    const cards   = boardEl ? Array.from(boardEl.querySelectorAll(".minion-card")) : [];

    currBoard.forEach((minion, idx) => {
      const card = cards[idx];
      if (!card) return;

      const prevMinion = prevBoard.find(m => m.name === minion.name);

      if (!prevMinion) {
        card.classList.add("summon-anim");
        card.addEventListener("animationend", () => card.classList.remove("summon-anim"), { once: true });
      } else {
        if (minion.hp < prevMinion.hp) {
          const dmg = prevMinion.hp - minion.hp;
          card.classList.add("damage-flash");
          card.addEventListener("animationend", () => card.classList.remove("damage-flash"), { once: true });
          spawnFloat(`-${dmg}`, "var(--col-dmg)", card, "big");
        } else if (minion.hp > prevMinion.hp) {
          const heal = minion.hp - prevMinion.hp;
          card.classList.add("buff-glow");
          card.addEventListener("animationend", () => card.classList.remove("buff-glow"), { once: true });
          spawnFloat(`+${heal}♥`, "var(--col-heal)", card, "normal");
        }
        // ATK changes are checked independently so both ATK and HP floats show
        // (e.g. Blessing gives +2/+2 — both changes should be visible)
        if (minion.atk > prevMinion.atk) {
          if (minion.hp >= prevMinion.hp) {
            card.classList.add("buff-glow");
            card.addEventListener("animationend", () => card.classList.remove("buff-glow"), { once: true });
          }
          spawnFloat(`+ATK`, "var(--col-gold)", card, "small");
        }
      }
    });
  });
}

/** Flash a hero panel briefly (damage taken) */
function flashHero(elId) {
  const el = document.getElementById(elId);
  if (!el) return;
  el.classList.add("hero-flash");
  el.addEventListener("animationend", () => el.classList.remove("hero-flash"), { once: true });
}

/** Detect hero HP changes and flash accordingly, spawning anchored floats */
function applyHeroAnimations(prev) {
  if (!prev || !gameState) return;
  if (gameState.p1.hp < prev.p1) {
    const dmg = prev.p1 - gameState.p1.hp;
    flashHero("hero-player");
    spawnFloat(`-${dmg}`, "var(--col-dmg)", document.getElementById("hero-player"), "big");
  } else if (gameState.p1.hp > prev.p1) {
    const heal = gameState.p1.hp - prev.p1;
    spawnFloat(`+${heal}♥`, "var(--col-heal)", document.getElementById("hero-player"), "normal");
  }
  if (gameState.p2.hp < prev.p2) {
    const dmg = prev.p2 - gameState.p2.hp;
    flashHero("hero-opp");
    spawnFloat(`-${dmg}`, "var(--col-dmg)", document.getElementById("hero-opp"), "big");
  } else if (gameState.p2.hp > prev.p2) {
    const heal = gameState.p2.hp - prev.p2;
    spawnFloat(`+${heal}♥`, "var(--col-heal)", document.getElementById("hero-opp"), "normal");
  }
}

// ---------------------------------------------------------------------------
// GAME RENDERING
// ---------------------------------------------------------------------------

function renderGame() {
  if (!gameState) return;
  const { p1, p2, is_player_turn, log, winner } = gameState;

  renderHero("hero-opp",    p2, true);
  renderHero("hero-player", p1, false);
  renderHeroMana("tray-player", p1);
  renderHeroMana("tray-opp", p2);
  renderHeroPower("hp-opp",    p2, true);
  renderHeroPower("hp-player", p1, false);
  renderDeckPanel("deck-opp",    p2);
  renderDeckPanel("deck-player", p1);
  renderOppHand(p2);
  renderBoard("board-opp",    p2, true);
  renderBoard("board-player", p1, false);
  renderHand(p1);
  renderLog(log);

  // Your-turn highlight
  document.getElementById("tray-player").classList.toggle("your-turn", !!is_player_turn && !winner);

  const etBtn = document.getElementById("btn-end-turn");
  etBtn.disabled = !is_player_turn || !!winner;
  etBtn.textContent = is_player_turn ? "End Turn" : "Waiting…";

  // Turn banner: fire only when turn ownership changes
  if (!winner && prevIsPlayerTurn !== null && prevIsPlayerTurn !== is_player_turn) {
    if (is_player_turn) turnNumber++;
    showTurnBanner(is_player_turn);
  }
  prevIsPlayerTurn = is_player_turn;

  // Turn counter badge
  const tcBadge = document.getElementById("turn-counter");
  if (tcBadge) tcBadge.textContent = turnNumber > 0 ? `Turn ${turnNumber}` : "";

  // Winner overlay
  const overlay = document.getElementById("winner-overlay");
  if (winner) {
    overlay.classList.remove("hidden");
    document.getElementById("winner-text").textContent =
      winner === "DRAW"   ? "It's a Draw!" :
      winner === "Player" ? "Victory!"      : "Defeat!";
  } else {
    overlay.classList.add("hidden");
  }

  updateSelectionInfo();
}

/* ---- Hero panel ---- */
function renderHero(elId, player, isOpp) {
  const el = document.getElementById(elId);

  const hpPct = Math.max(0, Math.min(100, (player.hp / 30) * 100));
  const icons = { Mage: "🔮", Warrior: "⚔️", Priest: "✨" };
  const icon  = icons[player.hero_class] || "?";
  const accentColor = HERO_COLORS[player.hero_class] || "#2e4a66";

  let cls = "hero-panel";
  if (!isOpp) {
    const canAtk = player.weapon && player.hero_can_attack;
    if (canAtk && !selected) cls += " attackable";
    if (selected?.type === "hero_weapon") cls += " selected";
  }

  if (selected && isValidHeroTarget(isOpp)) cls += " valid-target";
  if (player.hp <= 10) cls += " low-hp";

  let armorBadge  = player.armor > 0
    ? `<div class="armor-badge">${player.armor}</div>` : "";
  let weaponBadge = player.weapon
    ? `<div class="weapon-badge">${player.weapon.atk}⚔ ${player.weapon.durability}🛡</div>` : "";

  el.className    = cls;
  el.dataset.class = player.hero_class;

  // Accent glow via inline border color
  if (selected && isValidHeroTarget(isOpp)) {
    el.style.borderColor = "";
  } else if (!isOpp && selected?.type === "hero_weapon") {
    el.style.borderColor = "";
  } else {
    el.style.borderColor = accentColor;
  }

  el.innerHTML = `
    ${armorBadge}${weaponBadge}
    <div class="hero-icon">${icon}</div>
    <div class="hero-class-name">${player.hero_class}</div>
    <div class="hero-hp-bar"><div class="hero-hp-fill" style="width:${hpPct}%"></div></div>
    <div class="hero-hp-text">${Math.max(0, player.hp)} HP</div>
  `;

  el.onclick = () => handleHeroClick(isOpp, player);
}

function isValidHeroTarget(isOpp) {
  if (!selected) return false;
  const lm = getLegalMoves();
  if (!lm) return false;

  let actionType = null;
  if (selected.type === "hand")         actionType = "play";
  if (selected.type === "board")        actionType = "attack";
  if (selected.type === "hero_power")   actionType = "hero_power";
  if (selected.type === "hero_weapon")  actionType = "hero_attack";

  if ((actionType === "attack" || actionType === "hero_attack") && !isOpp) return false;
  if (actionType === "play") {
    const card = CARD_DB[gameState.p1.hand[selected.idx]];
    if (card?.effect === "damage" && !isOpp) return false;
  }
  if (actionType === "hero_power") {
    if (gameState.p1.hero_class === "Priest" &&  isOpp) return false;
    if (gameState.p1.hero_class === "Mage"   && !isOpp) return false;
  }

  return lm.some(([a, i, t]) =>
    a === actionType &&
    (selected.idx === undefined || i === selected.idx) &&
    t === "hero"
  );
}

function isValidMinionTarget(boardIdx, isOpp) {
  if (!selected) return false;
  const lm = getLegalMoves();
  if (!lm) return false;

  let actionType = null;
  if (selected.type === "hand")        actionType = "play";
  if (selected.type === "board")       actionType = "attack";
  if (selected.type === "hero_power")  actionType = "hero_power";
  if (selected.type === "hero_weapon") actionType = "hero_attack";
  if (!actionType) return false;

  if ((actionType === "attack" || actionType === "hero_attack") && !isOpp) return false;
  if (actionType === "play") {
    const card = CARD_DB[gameState.p1.hand[selected.idx]];
    if (card?.effect === "buff"   &&  isOpp) return false;
    if (card?.effect === "damage" && !isOpp) return false;
  }
  if (actionType === "hero_power") {
    if (gameState.p1.hero_class === "Priest" &&  isOpp) return false;
    if (gameState.p1.hero_class === "Mage"   && !isOpp) return false;
  }

  return lm.some(([a, i, t]) =>
    a === actionType &&
    (selected.idx === undefined || i === selected.idx) &&
    t === boardIdx
  );
}

/* ---- Mana gems ---- */
function renderHeroMana(trayId, player) {
  const tray = document.getElementById(trayId);
  let manaEl = tray.querySelector(".mana-bar");
  if (!manaEl) {
    manaEl = document.createElement("div");
    manaEl.className = "mana-bar";
    tray.appendChild(manaEl);
  }
  let gems = "";
  for (let i = 0; i < 10; i++) {
    const filled = i < player.mana ? " filled" : (i < player.max_mana ? "" : " empty");
    gems += `<div class="mana-gem${filled}"></div>`;
  }
  manaEl.innerHTML = `<span>${player.mana}/${player.max_mana}</span><div class="mana-gems">${gems}</div>`;
}

/* ---- Hero Power ---- */
function renderHeroPower(elId, player, isOpp) {
  const el = document.getElementById(elId);
  const canUse = !player.hero_power_used && player.mana >= 2;
  const icons  = { Mage: "🔥", Warrior: "🛡️", Priest: "💚" };
  const icon   = icons[player.hero_class] || "⚡";

  let cls = "hero-power-panel";
  if (!canUse) cls += " used";
  if (!isOpp && selected?.type === "hero_power") cls += " selected";

  const labels = { Mage: "Fireblast", Warrior: "Armor Up", Priest: "Heal" };
  el.className = cls;
  el.dataset.class = player.hero_class;
  el.innerHTML = `<div class="hp-icon">${icon}</div><div class="hp-cost">${labels[player.hero_class]}<br>2 Mana</div>`;

  if (!isOpp) {
    el.onclick = () => handleHeroPowerClick(player, canUse);
  }
}

/* ---- Deck panel ---- */
function renderDeckPanel(elId, player) {
  const el = document.getElementById(elId);
  el.innerHTML = `<div class="deck-n">${player.deck.length}</div><div>Deck</div>`;
}

/* ---- Opp hand ---- */
function renderOppHand(p2) {
  const el = document.getElementById("hand-opp");
  el.innerHTML = "";
  for (let i = 0; i < p2.hand.length; i++) {
    const card = document.createElement("div");
    card.className = "hand-opp-card";
    el.appendChild(card);
  }
}

/* ---- Board ---- */
function renderBoard(elId, player, isOpp) {
  const el = document.getElementById(elId);
  el.innerHTML = "";

  if (player.board.length === 0) {
    const hint = document.createElement("div");
    hint.className = "board-empty-hint";
    hint.textContent = isOpp ? "No minions" : "Play minions here";
    el.appendChild(hint);
  }

  player.board.forEach((minion, idx) => {
    const card = CARD_DB[minion.name] || {};
    const icon = CARD_EMOJIS[card.icon] || card.icon || "?";

    let cls = "minion-card";
    if (!isOpp && minion.can_attack && !selected)                      cls += " can-attack";
    if (!isOpp && selected?.type === "board" && selected.idx === idx)  cls += " selected";
    if (minion.taunt)                                                   cls += " taunt";
    if (minion.divine_shield)                                           cls += " divine-shield";
    if (!minion.can_attack && !isOpp)                                   cls += " exhausted";

    if (selected) {
      const valid = isValidMinionTarget(idx, isOpp);
      if (valid) cls += " valid-target";
      else if (isOpp) cls += " invalid-target";
    }

    const kws = KW_SHORT.filter(([k]) => minion[k]).map(([k, l]) =>
      `<span class="kw-badge" style="background:${KW_COLORS[k]};color:#fff">${l}</span>`
    ).join("");

    const div = document.createElement("div");
    div.className = cls;
    div.innerHTML = `
      <div class="minion-art">${icon}</div>
      <div class="minion-name">${minion.name}</div>
      <div class="kw-badges">${kws}</div>
      <div class="stat-badge atk">${minion.atk}</div>
      <div class="stat-badge hp">${minion.hp}</div>
    `;

    div.addEventListener("click", () => handleMinionClick(idx, isOpp, player, minion));
    div.addEventListener("mouseenter", e => showGameTooltip(e, minion.name, {...card, ...{atk:minion.atk, hp:minion.hp}}));
    div.addEventListener("mouseleave", () => hideTooltip("game-tooltip"));
    el.appendChild(div);
  });
}

/* ---- Player hand — with card fan effect ---- */
function renderHand(p1) {
  const el = document.getElementById("hand-player");
  el.innerHTML = "";

  // Hand size badge
  if (p1.hand.length > 0) {
    const badge = document.createElement("div");
    badge.className = "hand-size-badge";
    badge.textContent = `${p1.hand.length}/10`;
    el.appendChild(badge);
  }

  const total  = p1.hand.length;
  const midIdx = (total - 1) / 2;

  p1.hand.forEach((name, idx) => {
    const card       = CARD_DB[name] || {};
    const affordable = p1.mana >= card.cost;
    const icon       = CARD_EMOJIS[card.icon] || card.icon || "?";

    let cls = `hand-card hand-card--${card.type}`;
    if (!affordable)                                       cls += " unaffordable";
    if (selected?.type === "hand" && selected.idx === idx) cls += " selected";

    let extra = "";
    if (card.type === "minion" || card.type === "weapon") {
      const atkVal = card.atk;
      const hpVal  = card.type === "weapon" ? card.durability : card.hp;
      extra = `<div class="stat-badge atk">${atkVal}</div>
               <div class="stat-badge hp">${hpVal}</div>`;
    }

    const kws = card.type === "minion"
      ? KW_SHORT.filter(([k]) => card[k]).map(([k, l]) =>
          `<span class="kw-badge" style="background:${KW_COLORS[k]};color:#fff">${l}</span>`
        ).join("")
      : "";

    const div = document.createElement("div");
    div.className = cls;

    // Fan rotation: cards spread outward from center
    const rot = total > 1 ? (idx - midIdx) * 3.5 : 0;
    div.style.setProperty("--card-rot", `${rot}deg`);
    // Slight arc: outer cards lift down a bit
    const lift = total > 1 ? Math.abs(idx - midIdx) * 4 : 0;
    div.style.marginBottom = `${lift}px`;

    div.innerHTML = `
      <div class="gem-cost">${card.cost}</div>
      <div class="minion-art">${icon}</div>
      <div class="minion-name">${name}</div>
      <div class="kw-badges">${kws}</div>
      ${card.type === "spell" ? `<div class="pool-desc">${spellDesc(card, true)}</div>` : ""}
      ${extra}
    `;

    div.addEventListener("click", () => handleHandClick(idx, p1, name, card, affordable));
    div.addEventListener("mouseenter", e => showGameTooltip(e, name, card));
    div.addEventListener("mouseleave", () => hideTooltip("game-tooltip"));
    el.appendChild(div);
  });
}

/* ---- Combat log ---- */
function renderLog(entries) {
  const el = document.getElementById("log-entries");
  const wasAtBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 30;
  el.innerHTML = "";
  entries.slice(-60).forEach(msg => {
    const div = document.createElement("div");
    let cls = "log-entry";
    const m = msg.toLowerCase();
    if (m.includes("damage") || m.includes("attacks") || m.includes("fatigue") ||
        m.includes("destroys") || m.includes("dmg") || m.includes("d.rattle")) {
      cls += " log-dmg";
    } else if (m.includes("heal") || m.includes("restores") || m.includes("b.cry")) {
      cls += " log-heal";
    } else if (m.includes("plays")) {
      cls += " log-play";
    } else if (m.includes("armor") || m.includes("equipped")) {
      cls += " log-armor";
    } else if (m.includes("draws") || m.includes("draw")) {
      cls += " log-draw";
    } else if (m.includes("blocks") || m.includes("shield") || m.includes("blocked")) {
      cls += " log-block";
    } else if (m.includes("---") || m.includes("===") || m.includes("turn")) {
      cls += " log-system";
    }
    div.className = cls;
    div.textContent = msg;
    el.appendChild(div);
  });
  if (wasAtBottom) el.scrollTop = el.scrollHeight;
}

// ---------------------------------------------------------------------------
// SELECTION STATE
// ---------------------------------------------------------------------------
function clearSelection() {
  selected = null;
  updateSelectionInfo();
  renderGame();
}

function updateSelectionInfo() {
  const el = document.getElementById("selection-info");
  if (!selected) { el.classList.add("hidden"); return; }
  el.classList.remove("hidden");
  if (selected.type === "hand")        el.textContent = `Playing: ${gameState.p1.hand[selected.idx]} — click a target`;
  if (selected.type === "board")       el.textContent = `Attacking with: ${gameState.p1.board[selected.idx].name} — click a target`;
  if (selected.type === "hero_power")  el.textContent = "Hero Power — click a target";
  if (selected.type === "hero_weapon") el.textContent = "Hero Attack — click a target";
}

function getLegalMoves() {
  return gameState?._legal_moves || null;
}

// ---------------------------------------------------------------------------
// CLICK HANDLERS
// ---------------------------------------------------------------------------
function handleHandClick(idx, p1, name, card, affordable) {
  if (!gameState.is_player_turn || gameState.winner) return;
  if (!affordable) {
    const handEl = document.getElementById("hand-player");
    const cards  = handEl ? handEl.querySelectorAll(".hand-card") : [];
    const anchorEl = cards[idx] || null;
    spawnFloat("Not enough mana!", "var(--col-mana-bright)", anchorEl, "small");
    shakeElement(cards[idx]);
    return;
  }

  if (selected?.type === "hand" && selected.idx === idx) {
    clearSelection();
    return;
  }
  clearSelection();

  if (card.type === "minion") {
    if (p1.board.length >= 7) { spawnFloat("Board is full!", "var(--col-red)", null, "normal"); return; }
    sendAction("play", idx, null);
    return;
  }
  if (card.type === "weapon") {
    sendAction("play", idx, null);
    return;
  }
  if (card.type === "spell") {
    if (["heal", "draw", "damage_all"].includes(card.effect)) {
      sendAction("play", idx, null);
      return;
    }
    selected = { type: "hand", idx };
    renderGame();
  }
}

function shakeElement(el) {
  if (!el) return;
  el.classList.remove("shake");
  void el.offsetWidth;
  el.classList.add("shake");
  el.addEventListener("animationend", () => el.classList.remove("shake"), { once: true });
}

function handleMinionClick(idx, isOpp, player, minion) {
  if (!gameState.is_player_turn || gameState.winner) return;

  if (selected) {
    const targetValid = isValidMinionTarget(idx, isOpp);
    if (!targetValid) {
      spawnFloat("Invalid target!", "var(--col-red)", null, "normal");
      // Shake the clicked element
      const boardEl = document.getElementById(isOpp ? "board-opp" : "board-player");
      const cards   = boardEl ? boardEl.querySelectorAll(".minion-card") : [];
      shakeElement(cards[idx]);
      return;
    }

    let action;
    if (selected.type === "hand")        action = ["play",       selected.idx, idx];
    if (selected.type === "board")       action = ["attack",     selected.idx, idx];
    if (selected.type === "hero_power")  action = ["hero_power", null,         idx];
    if (selected.type === "hero_weapon") action = ["hero_attack",null,         idx];
    if (action) { clearSelection(); sendAction(...action); }
    return;
  }

  if (!isOpp && minion.can_attack) {
    selected = { type: "board", idx };
    renderGame();
  }
}

function handleHeroClick(isOpp, player) {
  if (!gameState.is_player_turn || gameState.winner) return;

  if (selected) {
    if (!isValidHeroTarget(isOpp)) {
      spawnFloat("Invalid target!", "var(--col-red)", null, "normal");
      shakeElement(document.getElementById(isOpp ? "hero-opp" : "hero-player"));
      return;
    }

    let action;
    if (selected.type === "hand")        action = ["play",       selected.idx, "hero"];
    if (selected.type === "board")       action = ["attack",     selected.idx, "hero"];
    if (selected.type === "hero_power")  action = ["hero_power", null,         "hero"];
    if (selected.type === "hero_weapon") action = ["hero_attack",null,         "hero"];
    if (action) { clearSelection(); sendAction(...action); }
    return;
  }

  if (!isOpp && player.weapon && player.hero_can_attack) {
    selected = { type: "hero_weapon" };
    renderGame();
  }
}

function handleHeroPowerClick(player, canUse) {
  if (!gameState.is_player_turn || gameState.winner) return;
  if (!canUse) {
    const msg = player.hero_power_used ? "Already used!" : "Not enough mana!";
    spawnFloat(msg, "var(--col-purple-bright)", null, "small");
    return;
  }

  if (selected?.type === "hero_power") { clearSelection(); return; }
  clearSelection();

  if (player.hero_class === "Warrior") { sendAction("hero_power", null, null); return; }
  selected = { type: "hero_power" };
  renderGame();
}

// Right-click / Escape to cancel
document.addEventListener("keydown", e => { if (e.key === "Escape") clearSelection(); });
document.addEventListener("contextmenu", e => {
  if (document.getElementById("screen-game")?.classList.contains("active")) {
    e.preventDefault();
    clearSelection();
  }
});

document.querySelectorAll(".hero-card").forEach(card => {
  card.addEventListener("keydown", e => {
    if (e.key !== "Enter" && e.key !== " ") return;
    e.preventDefault();
    const cls = card.dataset.class;
    if (cls) selectClass(cls);
  });
});

// ---------------------------------------------------------------------------
// API CALLS
// ---------------------------------------------------------------------------
async function sendAction(action, idx, target) {
  if (isActing || !gameState?.is_player_turn) return;
  isActing = true;

  const etBtn = document.getElementById("btn-end-turn");
  etBtn.disabled = true;

  const prevSnap   = snapshotBoards();
  const prevHeroHp = { p1: gameState.p1.hp, p2: gameState.p2.hp };

  try {
    const res = await fetch("/api/action", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, idx, target }),
    });
    const data = await res.json();
    if (data.error) {
      spawnFloat(data.error, "var(--col-red)", null, "normal");
    } else {
      CARD_DB   = data.card_db || CARD_DB;
      gameState = data;
      renderGame();
      applyPostRenderAnimations(prevSnap);
      applyHeroAnimations(prevHeroHp);
    }
  } catch (err) {
    spawnFloat("Network error!", "var(--col-red)", null, "normal");
  } finally {
    isActing = false;
    if (gameState?.is_player_turn && !gameState?.winner) etBtn.disabled = false;
  }
}

async function endTurn() {
  if (isActing || !gameState?.is_player_turn) return;
  isActing = true;
  clearSelection();

  const etBtn = document.getElementById("btn-end-turn");
  etBtn.disabled = true;
  setAiThinking(true);

  const prevSnap   = snapshotBoards();
  const prevHeroHp = { p1: gameState.p1.hp, p2: gameState.p2.hp };

  try {
    const res  = await fetch("/api/action", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "end_turn", idx: null, target: null }),
    });
    const data = await res.json();
    // Guard: player may have resigned while the AI was thinking
    if (gameState === null) return;
    CARD_DB   = data.card_db || CARD_DB;
    gameState = data;
    setAiThinking(false);
    // The server processes the entire AI turn synchronously, so the client
    // never sees is_player_turn=false. Increment turn counter first so
    // renderGame() picks it up for the badge, then fire the banner.
    if (!gameState.winner) turnNumber++;
    renderGame();
    if (!gameState.winner) showTurnBanner(true);
    applyPostRenderAnimations(prevSnap);
    applyHeroAnimations(prevHeroHp);
  } catch (err) {
    spawnFloat("Network error!", "var(--col-red)", null, "normal");
    setAiThinking(false);
    etBtn.textContent = "End Turn";
    etBtn.disabled = false;
  } finally {
    isActing = false;
  }
}

function resign() {
  if (!confirm("Resign and return to menu?")) return;
  resetGameState();
  showScreen("screen-menu");
}

function returnToMenu() {
  resetGameState();
  showScreen("screen-menu");
}

function resetGameState() {
  gameState        = null;
  selected         = null;
  prevIsPlayerTurn = null;
  turnNumber       = 0;
  isActing         = false;
  setAiThinking(false);
}

// ---------------------------------------------------------------------------
// FLOATING TEXT FX
// ---------------------------------------------------------------------------
/**
 * Spawn a floating text FX.
 * @param {string} text   - Text to display
 * @param {string} color  - CSS color string
 * @param {Element|null} el - Anchor element (null = screen centre)
 * @param {"big"|"normal"|"small"|"block"} size - Visual size variant
 */
function spawnFloat(text, color, el, size = "normal") {
  const layer = document.getElementById("fx-layer");
  if (!layer) return;
  const div = document.createElement("div");
  div.className   = `float-text${size !== "normal" ? " " + size : ""}`;
  div.textContent = text;
  div.style.color = color;

  if (el) {
    const rect      = el.getBoundingClientRect();
    const layerRect = layer.getBoundingClientRect();
    const cx = rect.left + rect.width  / 2 - layerRect.left;
    const cy = rect.top  + rect.height / 4 - layerRect.top;
    // Add small random horizontal jitter so multiple floats don't stack exactly
    div.style.left = (cx + (Math.random() - .5) * 20) + "px";
    div.style.top  = cy + "px";
  } else {
    div.style.left = (window.innerWidth  / 2) + "px";
    div.style.top  = (window.innerHeight / 2 - 60) + "px";
  }

  layer.appendChild(div);
  div.addEventListener("animationend", () => div.remove());
}

// ---------------------------------------------------------------------------
// BOOT
// ---------------------------------------------------------------------------
(async function init() {
  try {
    const res  = await fetch("/api/cards");
    const data = await res.json();
    if (data.card_db) CARD_DB = data.card_db;
  } catch (_) {}

  showScreen("screen-menu");
})();
