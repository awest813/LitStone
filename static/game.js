/* ============================================================
   TinyStone — Frontend Game Logic (game.js)
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

const KW_COLORS = {
  taunt: "#e74c3c", divine_shield: "#f1c40f", charge: "#2ecc71",
  poisonous: "#9b59b6", battlecry: "#3498db", deathrattle: "#566573",
};
const KW_SHORT = [
  ["taunt","TAUNT"], ["divine_shield","SHIELD"], ["charge","CHARGE"],
  ["poisonous","POISON"], ["battlecry","B.CRY"], ["deathrattle","D.RATTLE"],
];
const CARD_EMOJIS = {
  PE:"🪚", GD:"🛡️", RD:"🪓", KN:"⚔️", PA:"🏰", DR:"🐉",
  SP:"🕷️", CL:"📖", BM:"💣", ZP:"⚡", BL:"💥", MD:"💚",
  IN:"🔍", CV:"🌊", BS:"✨", AX:"🪓",
};

// ---------------------------------------------------------------------------
// Screen helpers
// ---------------------------------------------------------------------------
function showScreen(id) {
  document.querySelectorAll(".screen").forEach(s => {
    s.classList.toggle("active", s.id === id);
    s.style.display = s.id === id ? "" : "none";
  });
  // Force the game screen into its grid layout
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
  const res  = await fetch("/api/new_game", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ hero_class: selectedClass, deck: draftDeck }),
  });
  const data = await res.json();
  CARD_DB    = data.card_db;
  gameState  = data;
  selected   = null;
  showScreen("screen-game");
  renderGame();
}

function goBack() {
  showScreen("screen-menu");
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

  return `
    <div class="tooltip-name">${name}</div>
    <div class="tooltip-type">${card.type.toUpperCase()} · ${card.cost} Mana</div>
    ${stats}
    ${kws}
  `;
}

function positionTooltip(el, x, y) {
  const W = window.innerWidth, H = window.innerHeight;
  const TW = 180, TH = 200;
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

  // Your-turn highlight on player tray
  document.getElementById("tray-player").classList.toggle("your-turn", !!is_player_turn && !winner);

  // End turn button
  const etBtn = document.getElementById("btn-end-turn");
  etBtn.disabled = !is_player_turn || !!winner;
  etBtn.textContent = is_player_turn ? "End Turn" : "Waiting…";

  // Winner overlay
  const overlay = document.getElementById("winner-overlay");
  if (winner) {
    overlay.classList.remove("hidden");
    document.getElementById("winner-text").textContent =
      winner === "DRAW" ? "It's a Draw!" :
      winner === "Player" ? "Victory!" : "Defeat!";
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

  let cls = "hero-panel";
  const lm = getLegalMoves();

  if (!isOpp) {
    // Can the hero attack?
    const canAtk = player.weapon && player.hero_can_attack;
    if (canAtk && !selected) cls += " attackable";
    if (selected?.type === "hero_weapon") cls += " selected";
  }

  if (selected && isValidHeroTarget(isOpp)) cls += " valid-target";
  if (player.hp <= 10) cls += " low-hp";

  let armorBadge = player.armor > 0
    ? `<div class="armor-badge">${player.armor}</div>` : "";
  let weaponBadge = player.weapon
    ? `<div class="weapon-badge">${player.weapon.atk}⚔ ${player.weapon.durability}🛡</div>` : "";

  el.className = cls;
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

  // Attacks and hero-attacks always target the opponent's hero
  if ((actionType === "attack" || actionType === "hero_attack") && !isOpp) return false;
  // Damage spells target the opponent's hero
  if (actionType === "play") {
    const card = CARD_DB[gameState.p1.hand[selected.idx]];
    if (card?.effect === "damage" && !isOpp) return false;
  }
  // Priest heals own hero; Mage's Fireblast targets the opponent's hero
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

  // Attacks and hero-attacks always target the opponent's board
  if ((actionType === "attack" || actionType === "hero_attack") && !isOpp) return false;
  if (actionType === "play") {
    const card = CARD_DB[gameState.p1.hand[selected.idx]];
    if (card?.effect === "buff"   &&  isOpp) return false; // buff targets own board
    if (card?.effect === "damage" && !isOpp) return false; // damage targets opp board
  }
  // Priest heals own board; Mage's Fireblast targets the opponent's board
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
  // Find or create mana bar inside tray
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
  const icons = { Mage: "🔥", Warrior: "🛡️", Priest: "💚" };
  const icon  = icons[player.hero_class] || "⚡";

  let cls = "hero-power-panel";
  if (!canUse) cls += " used";
  if (!isOpp && selected?.type === "hero_power") cls += " selected";

  const labels = { Mage: "Fireblast", Warrior: "Armor Up", Priest: "Heal" };
  el.className = cls;
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

  player.board.forEach((minion, idx) => {
    const card = CARD_DB[minion.name] || {};
    const icon = CARD_EMOJIS[card.icon] || card.icon || "?";

    let cls = "minion-card";
    if (!isOpp && minion.can_attack && !selected)           cls += " can-attack";
    if (!isOpp && selected?.type === "board" && selected.idx === idx) cls += " selected";
    if (minion.taunt)                                        cls += " taunt";
    if (minion.divine_shield)                                cls += " divine-shield";
    if (!minion.can_attack && !isOpp)                        cls += " exhausted";

    // Targeting highlight
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

/* ---- Player hand ---- */
function renderHand(p1) {
  const el = document.getElementById("hand-player");
  el.innerHTML = "";

  p1.hand.forEach((name, idx) => {
    const card       = CARD_DB[name] || {};
    const affordable = p1.mana >= card.cost;
    const icon       = CARD_EMOJIS[card.icon] || card.icon || "?";

    let cls = `hand-card hand-card--${card.type}`;
    if (!affordable)                                   cls += " unaffordable";
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
  el.innerHTML = "";
  entries.slice(-40).forEach(msg => {
    const div = document.createElement("div");
    let cls = "log-entry";
    if (msg.includes("attacks") || msg.includes("damage") || msg.includes("FATIGUE") || msg.includes("destroys")) cls += " log-dmg";
    else if (msg.includes("heal") || msg.includes("Heal") || msg.includes("Restores")) cls += " log-heal";
    else if (msg.includes("plays")) cls += " log-play";
    else if (msg.includes("Armor") || msg.includes("Equipped")) cls += " log-armor";
    else if (msg.includes("draws") || msg.includes("Draw")) cls += " log-draw";
    else if (msg.includes("blocks") || msg.includes("Shield")) cls += " log-block";
    else if (msg.includes("---") || msg.includes("===")) cls += " log-system";
    div.className = cls;
    div.textContent = msg;
    el.appendChild(div);
  });
  el.scrollTop = el.scrollHeight;
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
  if (!affordable) { spawnFloat("Not enough mana!", "var(--col-mana)"); return; }

  if (selected?.type === "hand" && selected.idx === idx) {
    clearSelection();
    return;
  }
  clearSelection();

  // Cards that need no target: minions (placed automatically), buffs need friend target
  if (card.type === "minion") {
    if (p1.board.length >= 7) { spawnFloat("Board is full!", "var(--col-red)"); return; }
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
    // Needs a target
    selected = { type: "hand", idx };
    renderGame();
  }
}

function handleMinionClick(idx, isOpp, player, minion) {
  if (!gameState.is_player_turn || gameState.winner) return;

  // If we have a selection waiting for a target
  if (selected) {
    const targetValid = isValidMinionTarget(idx,
      isOpp && !(selected.type === "hand" && CARD_DB[gameState.p1.hand[selected.idx]]?.effect === "buff"));

    if (!targetValid) { spawnFloat("Invalid target!", "var(--col-red)"); return; }

    let action;
    if (selected.type === "hand")        action = ["play",       selected.idx, idx];
    if (selected.type === "board")       action = ["attack",     selected.idx, idx];
    if (selected.type === "hero_power")  action = ["hero_power", null,         idx];
    if (selected.type === "hero_weapon") action = ["hero_attack",null,         idx];
    if (action) { clearSelection(); sendAction(...action); }
    return;
  }

  // Select own minion to attack
  if (!isOpp && minion.can_attack) {
    selected = { type: "board", idx };
    renderGame();
  }
}

function handleHeroClick(isOpp, player) {
  if (!gameState.is_player_turn || gameState.winner) return;

  if (selected) {
    if (!isValidHeroTarget(isOpp)) { spawnFloat("Invalid target!", "var(--col-red)"); return; }

    let action;
    if (selected.type === "hand")        action = ["play",       selected.idx, "hero"];
    if (selected.type === "board")       action = ["attack",     selected.idx, "hero"];
    if (selected.type === "hero_power")  action = ["hero_power", null,         "hero"];
    if (selected.type === "hero_weapon") action = ["hero_attack",null,         "hero"];
    if (action) { clearSelection(); sendAction(...action); }
    return;
  }

  // Select own hero for weapon attack
  if (!isOpp && player.weapon && player.hero_can_attack) {
    selected = { type: "hero_weapon" };
    renderGame();
  }
}

function handleHeroPowerClick(player, canUse) {
  if (!gameState.is_player_turn || gameState.winner) return;
  if (!canUse) { spawnFloat("Already used / not enough mana!", "var(--col-purple)"); return; }

  if (selected?.type === "hero_power") { clearSelection(); return; }
  clearSelection();

  // Warrior: no target
  if (player.hero_class === "Warrior") { sendAction("hero_power", null, null); return; }
  // Priest heals friendly — still needs selection
  selected = { type: "hero_power" };
  renderGame();
}

// Right-click / Escape to cancel
document.addEventListener("keydown", e => { if (e.key === "Escape") clearSelection(); });
document.addEventListener("contextmenu", e => { e.preventDefault(); clearSelection(); });

// ---------------------------------------------------------------------------
// API CALLS
// ---------------------------------------------------------------------------
async function sendAction(action, idx, target) {
  if (!gameState?.is_player_turn) return;
  const etBtn = document.getElementById("btn-end-turn");
  etBtn.disabled = true;

  try {
    const res = await fetch("/api/action", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, idx, target }),
    });
    const data = await res.json();
    if (data.error) {
      spawnFloat(data.error, "var(--col-red)");
    } else {
      CARD_DB    = data.card_db || CARD_DB;
      gameState  = data;
      renderGame();
      if (data.winner) return;
    }
  } catch (err) {
    spawnFloat("Network error!", "var(--col-red)");
  } finally {
    if (gameState?.is_player_turn) etBtn.disabled = false;
  }
}

async function endTurn() {
  if (!gameState?.is_player_turn) return;
  clearSelection();
  const etBtn = document.getElementById("btn-end-turn");
  etBtn.disabled = true;
  etBtn.textContent = "AI thinking…";

  try {
    const res  = await fetch("/api/action", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "end_turn", idx: null, target: null }),
    });
    const data = await res.json();
    CARD_DB   = data.card_db || CARD_DB;
    gameState = data;
    renderGame();
  } catch (err) {
    spawnFloat("Network error!", "var(--col-red)");
    etBtn.disabled = false;
  }
}

function resign() {
  if (!confirm("Resign and return to menu?")) return;
  gameState = null;
  selected  = null;
  showScreen("screen-menu");
}

function returnToMenu() {
  gameState = null;
  selected  = null;
  showScreen("screen-menu");
}

// ---------------------------------------------------------------------------
// FLOATING TEXT FX
// ---------------------------------------------------------------------------
function spawnFloat(text, color, x, y) {
  const layer = document.getElementById("fx-layer");
  const div   = document.createElement("div");
  div.className   = "float-text";
  div.textContent = text;
  div.style.color = color;
  div.style.left  = (x ?? window.innerWidth  / 2) + "px";
  div.style.top   = (y ?? window.innerHeight / 2 - 40) + "px";
  div.style.transform = "translateX(-50%)";
  layer.appendChild(div);
  div.addEventListener("animationend", () => div.remove());
}

// ---------------------------------------------------------------------------
// BOOT
// ---------------------------------------------------------------------------
(async function init() {
  // Pre-fetch card database so the deck builder works before any game is started
  try {
    const res  = await fetch("/api/cards");
    const data = await res.json();
    if (data.card_db) CARD_DB = data.card_db;
  } catch (_) {}

  showScreen("screen-menu");
})();
