/* ============================================================
   LitStone — Frontend Game Logic (game.js)
   All UI rendering, selection state, and server communication.
   ============================================================ */

"use strict";

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------
let CARD_DB   = {};          // injected on first server response
let DECK_SIZE = 30;          // synced from /api/cards
let gameId    = null;        // per-match session id from server
let gameState = null;        // latest server state snapshot
let selected  = null;        // { type: "hand"|"board"|"hero_power"|"hero_weapon", idx }
let draftDeck = [];
let selectedClass = null;

// Deck-builder UI state
let filterType  = "all";  // "all" | "minion" | "spell" | "weapon"
let filterCost  = "all";  // "all" | "1".."5" | "6plus"
let sortBy      = "cost"; // "cost" | "name"
let deckSearch  = "";
let combatLogOpen = true;
let isPaused    = false;
let lastMatchDeck = null; // { heroClass, cards } for Play Again
let logRenderedCount = 0;
let deckSearchTimer  = null;
let activeCampaignNode = null;
let campaignNodes = [];
let tutorialActive = false;
let tutorialStep = 0;
let practiceActive = false;
let practiceOptions = { p1_hp: 30, p2_hp: 30, infinite_mana: false };
const CAMPAIGN_PROGRESS_KEY = "litstoneCampaignProgress";
const TUTORIAL_DONE_KEY = "litstoneTutorialDone";

// Deck-builder constants
const MANA_CURVE_MAX_COST   = 7;   // buckets 1-7; costs ≥7 are grouped under "7+"
const MAX_AUTOFILL_ATTEMPTS = 500; // safety cap for the random auto-fill loop

// UI state
let isActing          = false; // prevents double-submit during server round-trips
let prevIsPlayerTurn  = null;  // tracks turn transitions for banner
let turnNumber        = 0;     // client-side turn counter
let audioCtx          = null;

const SETTINGS_KEY    = "litstoneSettings";
const LAST_DECK_KEY   = "litstoneLastDeck";

async function apiFetch(url, options = {}) {
  const res = await fetch(url, options);
  const text = await res.text();
  let data = {};
  if (text) {
    try {
      data = JSON.parse(text);
    } catch (_) {
      if (!res.ok) throw new Error(res.statusText || "Request failed");
      throw new Error("Invalid server response");
    }
  }
  if (!res.ok) {
    const err = new Error(data.error || res.statusText || "Request failed");
    err.data = data;
    err.status = res.status;
    throw err;
  }
  return data;
}

function defaultSettings() {
  return { sfx: true, animations: true, combatLog: true, confirmResign: true, gameSpeed: "normal" };
}

function loadSettings() {
  const legacyMuted = localStorage.getItem("litstoneMuted") === "1";
  try {
    const stored = JSON.parse(localStorage.getItem(SETTINGS_KEY) || "{}");
    const s = { ...defaultSettings(), ...stored };
    if (legacyMuted && stored.sfx === undefined) s.sfx = false;
    return s;
  } catch (_) {
    return { ...defaultSettings(), sfx: !legacyMuted };
  }
}

function saveSettings() {
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
  localStorage.setItem("litstoneMuted", settings.sfx ? "0" : "1");
}

let settings = loadSettings();
let sfxMuted = !settings.sfx;
let animationsEnabled = settings.animations !== false;
let gameSpeed = settings.gameSpeed || "normal";

function animMs(ms) {
  if (gameSpeed === "instant") return 0;
  if (gameSpeed === "fast") return Math.max(16, Math.round(ms * 0.45));
  return ms;
}

function aiAttackStaggerMs() {
  if (gameSpeed === "instant") return 0;
  if (gameSpeed === "fast") return 45;
  return 100;
}

function applyGameSpeedClass() {
  document.body.classList.remove("speed-normal", "speed-fast", "speed-instant");
  document.body.classList.add(`speed-${gameSpeed}`);
}

const KW_COLORS = {
  taunt: "#c0392b", divine_shield: "#d4a800", charge: "#00a878",
  poisonous: "#8e44ad", battlecry: "#2371b5", deathrattle: "#404e5c",
};
const KW_SHORT = [
  ["taunt","TAUNT"], ["divine_shield","SHIELD"], ["charge","CHARGE"],
  ["poisonous","POISON"], ["battlecry","B.CRY"], ["deathrattle","D.RATTLE"],
];
// Hero class accent colors
const HERO_COLORS = {
  Mage: "#2980b9", Warrior: "#c0392b", Priest: "#d4820a", Rogue: "#1abc9c", Paladin: "#c0a020", Shaman: "#0077b6",
};

// Hero class icons (used across multiple render functions)
const HERO_ICONS = {
  Mage: "🔮", Warrior: "⚔️", Priest: "✨", Rogue: "🗡️", Paladin: "🛡️", Shaman: "⚡",
};

// Hero power labels (used in renderHeroPower)
const HERO_POWER_LABELS = {
  Mage: "Fireblast", Warrior: "Armor Up", Priest: "Heal", Rogue: "Dagger", Paladin: "Reinforce", Shaman: "Totemic Call",
};

// Hero power icons
const HERO_POWER_ICONS = {
  Mage: "🔥", Warrior: "🛡️", Priest: "💚", Rogue: "🗡️", Paladin: "⚔️", Shaman: "🗿",
};

// ---------------------------------------------------------------------------
// Screen helpers
// ---------------------------------------------------------------------------
function showScreen(id) {
  if (id !== "screen-game") closePause(false);
  document.querySelectorAll(".screen").forEach(s => {
    const on = s.id === id;
    s.classList.toggle("active", on);
    if (!on) {
      s.style.display = "none";
      return;
    }
    if (id === "screen-game") s.style.display = "grid";
    else if (id === "screen-mulligan") s.style.display = "flex";
    else s.style.display = "";
  });
  if (id === "screen-game") initGameScreenUi();
  if (id === "screen-hub") updateHubContinue();
}

function isNarrowViewport() {
  return window.matchMedia("(max-width: 900px)").matches;
}

function initGameScreenUi() {
  combatLogOpen = isNarrowViewport() ? false : settings.combatLog !== false;
  applyCombatLogState();
  syncSfxButton();
}

function toggleCombatLog() {
  combatLogOpen = !combatLogOpen;
  applyCombatLogState();
}

function applyCombatLogState() {
  const log = document.getElementById("combat-log");
  const btn = document.getElementById("btn-log-toggle");
  if (log) log.classList.toggle("collapsed", !combatLogOpen);
  if (btn) {
    btn.setAttribute("aria-expanded", combatLogOpen ? "true" : "false");
    btn.textContent = combatLogOpen ? "📜 Hide Log" : "📜 Show Log";
  }
}

function updateGameHelpBar() {
  const bar = document.getElementById("game-help-bar");
  if (!bar || !gameState) return;
  if (gameState.winner) {
    bar.textContent = "";
    bar.classList.add("hidden");
    return;
  }
  bar.classList.remove("hidden");
  if (!gameState.is_player_turn) {
    bar.textContent = "Opponent is thinking…";
    return;
  }
  if (selected) return; // selection-info takes over
  const tut = tutorialHintText();
  if (tut) {
    bar.textContent = tut;
    return;
  }
  if (gameState.mode === "practice" && gameState.practice) {
    const p = gameState.practice;
    const mana = p.infinite_mana ? " · ∞ mana" : "";
    bar.textContent = `Practice — You ${p.p1_hp} HP · AI ${p.p2_hp} HP${mana}`;
    return;
  }
  if (gameState.mode === "campaign" && gameState.opponent_name) {
    bar.textContent = `vs ${gameState.opponent_name} · ${gameState.ai_difficulty} AI`;
    return;
  }
  bar.textContent = "Play from hand · Attack glowing minions · Esc or right-click to cancel";
}

function renderManaHud(p1) {
  const hud = document.getElementById("game-mana-hud");
  if (!hud || !p1) return;
  let gems = "";
  for (let i = 0; i < 10; i++) {
    const filled = i < p1.mana ? " filled" : (i < p1.max_mana ? "" : " empty");
    gems += `<div class="mana-gem mana-gem--hud${filled}" aria-hidden="true"></div>`;
  }
  hud.innerHTML = `
    <span class="mana-hud-label">Mana</span>
    <span class="mana-hud-count">${p1.mana}/${p1.max_mana}</span>
    <div class="mana-gems mana-gems--hud">${gems}</div>
  `;
}

// ---------------------------------------------------------------------------
// NAVIGATION — hub, class select, settings, pause
// ---------------------------------------------------------------------------
function goToHub() {
  practiceActive = false;
  activeCampaignNode = null;
  tutorialActive = false;
  tutorialStep = 0;
  showScreen("screen-hub");
}

function captureMatchContext() {
  const gs = gameState;
  return {
    campaignNode: gs?.campaign_node ?? activeCampaignNode,
    tutorial: !!(gs?.tutorial || gs?.mode === "tutorial" || tutorialActive),
    practice: gs?.mode === "practice" || practiceActive,
    practiceOptions: gs?.practice ? { ...gs.practice } : { ...practiceOptions },
  };
}

function applyMatchContext(ctx) {
  activeCampaignNode = ctx.campaignNode || null;
  tutorialActive = !!ctx.tutorial;
  practiceActive = !!ctx.practice;
  if (ctx.practiceOptions) practiceOptions = { ...ctx.practiceOptions };
}

function syncNavigationFromGameState(data) {
  if (!data?.mode) return;
  if (data.mode === "practice") {
    practiceActive = true;
    if (data.practice) practiceOptions = { ...data.practice };
  } else if (data.mode === "tutorial") {
    tutorialActive = true;
  } else if (data.mode === "campaign" && data.campaign_node) {
    activeCampaignNode = data.campaign_node;
  }
}

function goBackFromClassSelect() {
  if (practiceActive) {
    showScreen("screen-practice");
    return;
  }
  if (tutorialActive) {
    tutorialActive = false;
    tutorialStep = 0;
    goToHub();
    return;
  }
  if (activeCampaignNode) {
    goToCampaign();
    return;
  }
  goToHub();
}

function goToClassSelect() {
  showScreen("screen-menu");
}

function startStandardPlay() {
  practiceActive = false;
  activeCampaignNode = null;
  tutorialActive = false;
  goToClassSelect();
}

function goToPractice() {
  practiceActive = true;
  activeCampaignNode = null;
  tutorialActive = false;
  showScreen("screen-practice");
}

function startPracticeFromSetup() {
  const p1El = document.getElementById("practice-p1-hp");
  const p2El = document.getElementById("practice-p2-hp");
  const manaEl = document.getElementById("practice-infinite-mana");
  practiceOptions = {
    p1_hp: Math.max(1, Math.min(60, parseInt(p1El?.value, 10) || 30)),
    p2_hp: Math.max(1, Math.min(60, parseInt(p2El?.value, 10) || 30)),
    infinite_mana: !!manaEl?.checked,
  };
  const sub = document.getElementById("deck-subtitle");
  if (sub) {
    const mana = practiceOptions.infinite_mana ? " · infinite mana" : "";
    sub.textContent = `Practice — ${practiceOptions.p1_hp} HP vs AI ${practiceOptions.p2_hp} HP${mana}`;
  }
  const diffEl = document.getElementById("match-difficulty");
  if (diffEl) diffEl.value = "easy";
  goToClassSelect();
}

function getCampaignProgress() {
  try {
    return JSON.parse(localStorage.getItem(CAMPAIGN_PROGRESS_KEY) || "[]");
  } catch (_) {
    return [];
  }
}

function saveCampaignProgress(completedIds) {
  localStorage.setItem(CAMPAIGN_PROGRESS_KEY, JSON.stringify(completedIds));
}

function isCampaignNodeUnlocked(nodeId, completed) {
  const idx = campaignNodes.findIndex(n => n.id === nodeId);
  if (idx <= 0) return true;
  const prev = campaignNodes[idx - 1];
  return completed.includes(prev.id);
}

async function goToCampaign() {
  practiceActive = false;
  tutorialActive = false;
  try {
    const data = await apiFetch("/api/campaign");
    campaignNodes = data.nodes || [];
  } catch (_) {
    campaignNodes = [];
    showStatusToast("Could not load campaign. Try again.");
  }
  renderCampaignMap();
  showScreen("screen-campaign");
}

function renderCampaignMap() {
  const map = document.getElementById("campaign-map");
  if (!map) return;
  const completed = getCampaignProgress();
  map.innerHTML = "";
  campaignNodes.forEach((node, i) => {
    const unlocked = isCampaignNodeUnlocked(node.id, completed);
    const done = completed.includes(node.id);
    const isBoss = !!node.boss_id && node.id === "n5";
    const isElite = !!node.boss_id && !isBoss;
    let cls = "campaign-node";
    if (!unlocked) cls += " campaign-node--locked";
    if (done) cls += " campaign-node--done";
    if (isBoss) cls += " campaign-node--boss";
    if (isElite) cls += " campaign-node--elite";

    const div = document.createElement("button");
    div.type = "button";
    div.className = cls;
    div.disabled = !unlocked;
    const status = done ? "completed" : (unlocked ? "unlocked" : "locked");
    div.setAttribute("aria-label", `${node.name}, ${node.difficulty}, ${status}`);
    div.innerHTML = `
      <span class="campaign-node-index">${i + 1}</span>
      <span class="campaign-node-body">
        <div class="campaign-node-name">${node.name}</div>
        <div class="campaign-node-sub">${node.subtitle || ""}</div>
      </span>
      <span class="campaign-node-badge">${done ? "✓ Done" : node.difficulty}</span>
    `;
    if (unlocked) {
      div.addEventListener("click", () => startCampaignNode(node));
    }
    map.appendChild(div);
  });
}

function startCampaignNode(node) {
  activeCampaignNode = node.id;
  practiceActive = false;
  tutorialActive = false;
  const diffEl = document.getElementById("match-difficulty");
  if (diffEl && node.difficulty) diffEl.value = node.difficulty;
  const sub = document.getElementById("deck-subtitle");
  if (sub) sub.textContent = `Campaign: ${node.name} · ${node.difficulty} AI`;
  goToClassSelect();
}

async function startTutorial() {
  if (localStorage.getItem(TUTORIAL_DONE_KEY) === "1") {
    if (!confirm("Replay the tutorial?")) return;
  }
  activeCampaignNode = null;
  practiceActive = false;
  tutorialActive = true;
  tutorialStep = 0;
  const diffEl = document.getElementById("match-difficulty");
  if (diffEl) diffEl.value = "easy";
  enterDeckBuilder("Mage", []);
  loadStarterDeck();
  const sub = document.getElementById("deck-subtitle");
  if (sub) sub.textContent = "Tutorial — learn minions, attacks, and turns";
  await startGame();
}

function onCampaignVictory() {
  if (!activeCampaignNode || !gameState || gameState.winner !== "Player") return;
  const completed = getCampaignProgress();
  if (!completed.includes(activeCampaignNode)) {
    completed.push(activeCampaignNode);
    saveCampaignProgress(completed);
    showStatusToast("Campaign node cleared!");
  }
}

function advanceTutorialFromState() {
  if (!tutorialActive || !gameState) return;
  const p1 = gameState.p1;
  if (tutorialStep === 0 && p1.board.length > 0) {
    tutorialStep = 1;
  }
  if (tutorialStep === 1 && gameState.log) {
    const recent = gameState.log.slice(-8).join(" ").toLowerCase();
    if (recent.includes("attacks") && recent.includes("player")) {
      tutorialStep = 2;
    }
  }
  if (tutorialStep >= 2) {
    localStorage.setItem(TUTORIAL_DONE_KEY, "1");
    const btn = document.getElementById("btn-hub-tutorial");
    if (btn) btn.textContent = "Tutorial ✓";
  }
}

function tutorialHintText() {
  if (!tutorialActive) return null;
  if (tutorialStep === 0) return "Step 1 — Play a minion from your hand";
  if (tutorialStep === 1) return "Step 2 — Attack with a glowing minion";
  if (tutorialStep === 2) return "Step 3 — End turn or use Hero Power when ready";
  return "Tutorial complete — keep playing!";
}

function openSettings() {
  syncSettingsUi();
  const modal = document.getElementById("settings-modal");
  if (modal) modal.classList.remove("hidden");
}

function closeSettings() {
  document.getElementById("settings-modal")?.classList.add("hidden");
}

function openSettingsFromPause() {
  openSettings();
}

function syncSettingsUi() {
  const sfx = document.getElementById("setting-sfx");
  const anim = document.getElementById("setting-animations");
  const log = document.getElementById("setting-combat-log");
  const resign = document.getElementById("setting-confirm-resign");
  const speed = document.getElementById("setting-speed");
  if (sfx) sfx.checked = settings.sfx;
  if (anim) anim.checked = settings.animations;
  if (log) log.checked = settings.combatLog;
  if (resign) resign.checked = settings.confirmResign;
  if (speed) speed.value = gameSpeed;
}

function applySettingSfx(on) {
  settings.sfx = on;
  sfxMuted = !on;
  saveSettings();
  syncSfxButton();
  if (on) playSfx("turn");
}

function applySettingAnimations(on) {
  settings.animations = on;
  animationsEnabled = on;
  saveSettings();
}

function applySettingCombatLog(on) {
  settings.combatLog = on;
  saveSettings();
  if (document.getElementById("screen-game")?.classList.contains("active") && !isNarrowViewport()) {
    combatLogOpen = on;
    applyCombatLogState();
  }
}

function applySettingConfirmResign(on) {
  settings.confirmResign = on;
  saveSettings();
}

function applySettingSpeed(speed) {
  gameSpeed = ["normal", "fast", "instant"].includes(speed) ? speed : "normal";
  settings.gameSpeed = gameSpeed;
  saveSettings();
  applyGameSpeedClass();
}

function togglePause() {
  if (isPaused) closePause();
  else openPause();
}

function openPause() {
  if (!gameState || gameState.winner) return;
  if (document.getElementById("screen-game")?.classList.contains("active") === false) return;
  isPaused = true;
  clearSelection();
  document.getElementById("screen-game")?.classList.add("is-paused");
  document.getElementById("pause-overlay")?.classList.remove("hidden");
}

function closePause(focusGame = true) {
  isPaused = false;
  document.getElementById("screen-game")?.classList.remove("is-paused");
  document.getElementById("pause-overlay")?.classList.add("hidden");
  if (focusGame) document.getElementById("btn-pause")?.focus();
}

function resignFromPause() {
  closePause(false);
  resign();
}

function quitToHubFromPause() {
  closePause(false);
  if (settings.confirmResign && !confirm("Leave match and return to menu?")) return;
  abandonGame().then(() => goToHub());
}

function showLoading(text) {
  const el = document.getElementById("loading-overlay");
  const msg = document.getElementById("loading-text");
  if (msg) msg.textContent = text || "Loading…";
  el?.classList.remove("hidden");
  if (typeof NProgress !== "undefined") NProgress.start();
}

function hideLoading() {
  document.getElementById("loading-overlay")?.classList.add("hidden");
  if (typeof NProgress !== "undefined") NProgress.done();
}

function saveLastDeck() {
  if (!selectedClass || draftDeck.length !== DECK_SIZE) return;
  localStorage.setItem(LAST_DECK_KEY, JSON.stringify({
    heroClass: selectedClass,
    cards: [...draftDeck],
    savedAt: Date.now(),
  }));
}

function getLastDeck() {
  try {
    return JSON.parse(localStorage.getItem(LAST_DECK_KEY) || "null");
  } catch (_) {
    return null;
  }
}

function updateHubContinue() {
  const btn = document.getElementById("btn-hub-continue");
  const last = getLastDeck();
  if (!btn) return;
  if (last?.heroClass && last.cards?.length === DECK_SIZE) {
    btn.textContent = `Continue — ${last.heroClass} Deck`;
    btn.classList.remove("hidden");
  } else {
    btn.classList.add("hidden");
  }
}

function continueLastDeck() {
  const last = getLastDeck();
  if (!last?.heroClass || !last.cards) return;
  enterDeckBuilder(last.heroClass, last.cards);
}

function deckBuilderSubtitle(cls) {
  if (tutorialActive) return "Tutorial match · Easy AI · follow the hints";
  if (practiceActive) {
    const mana = practiceOptions.infinite_mana ? " · infinite mana" : "";
    return `Practice — ${practiceOptions.p1_hp} HP vs AI ${practiceOptions.p2_hp} HP${mana}`;
  }
  if (activeCampaignNode) {
    const node = campaignNodes.find(n => n.id === activeCampaignNode);
    if (node) return `Campaign: ${node.name} · ${node.difficulty} AI`;
  }
  return `${cls} + neutral cards · Max 2 copies · ${DECK_SIZE} cards total`;
}

function enterDeckBuilder(cls, initialDeck) {
  selectedClass = cls;
  draftDeck = initialDeck ? [...initialDeck] : [];
  filterType = "all";
  filterCost = "all";
  sortBy = "cost";
  deckSearch = "";
  clearTimeout(deckSearchTimer);
  const searchEl = document.getElementById("deck-search");
  if (searchEl) searchEl.value = "";
  document.getElementById("deck-title").textContent = `Build Your ${cls} Deck`;
  const sub = document.getElementById("deck-subtitle");
  if (sub) sub.textContent = deckBuilderSubtitle(cls);
  const emblem = document.getElementById("deck-class-emblem");
  if (emblem) {
    emblem.textContent = HERO_ICONS[cls] || "?";
    emblem.style.borderColor = HERO_COLORS[cls] || "var(--col-border-bright)";
    emblem.style.boxShadow = `0 0 14px ${HERO_COLORS[cls] || "#333"}55`;
  }
  document.querySelectorAll(".filter-btn").forEach(b => b.classList.toggle("active", b.dataset.filter === "all"));
  document.querySelectorAll(".sort-btn").forEach(b => b.classList.toggle("active", b.dataset.sort === "cost"));
  document.querySelectorAll(".cost-filter-btn").forEach(b => b.classList.toggle("active", b.dataset.cost === "all"));
  showScreen("screen-deck");
  renderCardPool();
  updateDeckSidebar();
  renderSavedDecks();
  updateDeckValidation();
}

function selectClass(cls) {
  if (!activeCampaignNode && !tutorialActive) {
    activeCampaignNode = null;
  }
  enterDeckBuilder(cls, []);
}

// ---------------------------------------------------------------------------
// DECK BUILDER
// ---------------------------------------------------------------------------
function setFilter(type) {
  filterType = type;
  document.querySelectorAll(".filter-btn").forEach(b => {
    const on = b.dataset.filter === type;
    b.classList.toggle("active", on);
    b.setAttribute("aria-pressed", on ? "true" : "false");
  });
  renderCardPool();
}

function setSort(sort) {
  sortBy = sort;
  document.querySelectorAll(".sort-btn").forEach(b => {
    const on = b.dataset.sort === sort;
    b.classList.toggle("active", on);
    b.setAttribute("aria-pressed", on ? "true" : "false");
  });
  renderCardPool();
}

function setDeckSearch(query) {
  deckSearch = (query || "").trim().toLowerCase();
  clearTimeout(deckSearchTimer);
  deckSearchTimer = setTimeout(() => renderCardPool(), 100);
}

function setCostFilter(cost) {
  filterCost = cost;
  document.querySelectorAll(".cost-filter-btn").forEach(b => {
    const on = b.dataset.cost === cost;
    b.classList.toggle("active", on);
    b.setAttribute("aria-pressed", on ? "true" : "false");
  });
  renderCardPool();
}

function cardMatchesCostFilter(card) {
  if (filterCost === "all") return true;
  const c = card.cost ?? 0;
  if (filterCost === "6plus") return c >= 6;
  return String(c) === filterCost;
}

function loadStarterDeck() {
  if (!selectedClass) return;
  const classCards = Object.entries(CARD_DB)
    .filter(([, c]) => c.classes?.includes(selectedClass) && !c.legendary && !c.uncollectible)
    .sort((a, b) => a[1].cost - b[1].cost || a[0].localeCompare(b[0]));
  const neutrals = Object.entries(CARD_DB)
    .filter(([, c]) => (!c.classes || c.classes.length === 0) && !c.legendary && !c.uncollectible)
    .sort((a, b) => a[1].cost - b[1].cost || a[0].localeCompare(b[0]));

  draftDeck = [];
  classCards.slice(0, 6).forEach(([name]) => {
    for (let i = 0; i < 2 && draftDeck.length < DECK_SIZE; i++) draftDeck.push(name);
  });
  let guard = 0;
  let ni = 0;
  while (draftDeck.length < DECK_SIZE && neutrals.length > 0 && guard < 600) {
    guard++;
    const [name] = neutrals[ni % neutrals.length];
    const max = CARD_DB[name]?.legendary ? 1 : 2;
    if (draftDeck.filter(c => c === name).length < max) draftDeck.push(name);
    ni++;
  }
  if (draftDeck.length < DECK_SIZE) autoFillDeck();
  else {
    renderCardPool();
    updateDeckSidebar();
  }
  showStatusToast("Starter deck loaded — tweak it or play!");
}

function updateDeckValidation() {
  const el = document.getElementById("deck-validation");
  if (!el) return;
  const n = draftDeck.length;
  const need = DECK_SIZE - n;
  el.className = "deck-validation";
  if (n === DECK_SIZE) {
    el.textContent = "✓ Deck ready — good luck!";
    el.classList.add("deck-validation--ok");
  } else if (n === 0) {
    el.textContent = `Add ${DECK_SIZE} cards or tap Starter / Fill`;
    el.classList.add("deck-validation--warn");
  } else {
    el.textContent = `Need ${need} more card${need === 1 ? "" : "s"}`;
    el.classList.add("deck-validation--warn");
  }
}

function cardAllowedForClass(card, heroClass) {
  if (card.uncollectible) return false;
  if (!card.classes || card.classes.length === 0) return true;
  return card.classes.includes(heroClass);
}

function poolCardNames() {
  return Object.entries(CARD_DB)
    .filter(([, card]) => cardAllowedForClass(card, selectedClass))
    .map(([name]) => name);
}

function filterPoolBySearch(entries, query) {
  const q = (query || "").trim();
  if (!q) return entries;

  if (typeof fuzzysort !== "undefined") {
    const items = entries.map(([name, card]) => ({
      name,
      type: card.type,
      desc: spellDesc(card, true),
      entry: [name, card],
    }));
    const hits = fuzzysort.go(q, items, {
      keys: ["name", "type", "desc"],
      threshold: -10000,
    });
    return hits.map(h => h.obj.entry);
  }

  const needle = q.toLowerCase();
  return entries.filter(([name, card]) => {
    const hay = `${name} ${card.type} ${spellDesc(card, true)}`.toLowerCase();
    return hay.includes(needle);
  });
}

function renderCardPool() {
  const pool = document.getElementById("card-pool");
  if (!pool) return;
  pool.innerHTML = "";

  let entries = Object.entries(CARD_DB).filter(([, card]) =>
    cardAllowedForClass(card, selectedClass)
  );

  // Apply type filter
  if (filterType !== "all") {
    entries = entries.filter(([, card]) => card.type === filterType);
  }

  if (filterCost !== "all") {
    entries = entries.filter(([, card]) => cardMatchesCostFilter(card));
  }

  if (deckSearch) {
    entries = filterPoolBySearch(entries, deckSearch);
  }

  if (entries.length === 0) {
    pool.innerHTML = `<div class="pool-empty-msg">No cards match your filters.</div>`;
    return;
  }

  // Apply sort
  if (sortBy === "cost") {
    entries.sort((a, b) => a[1].cost - b[1].cost || a[0].localeCompare(b[0]));
  } else {
    entries.sort((a, b) => a[0].localeCompare(b[0]));
  }

  const frag = document.createDocumentFragment();
  entries.forEach(([name, card]) => {
    const isLegendary = !!card.legendary;
    const maxCopies  = isLegendary ? 1 : 2;
    const count  = draftDeck.filter(c => c === name).length;
    const isFull = count >= maxCopies || draftDeck.length >= DECK_SIZE;
    const div    = document.createElement("div");
    const isClass = card.classes?.length > 0;
    div.className = `pool-card pool-card--${card.type}${isFull ? " pool-card--full" : ""}${isLegendary ? " pool-card--legendary" : ""}${isClass ? " pool-card--class" : ""} ${CardArt.frameClasses(card, name)}`;
    div.dataset.name = name;

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
      ${isLegendary ? `<div class="legendary-crown" title="Legendary — only 1 copy per deck">♦</div>` : ""}
      ${isClass ? `<div class="class-badge" title="${card.classes.join(", ")} only">${card.classes[0].slice(0,3)}</div>` : ""}
      ${CardArt.renderArt(card, name, "pool")}
      <div class="pool-name">${name}</div>
      ${statsHtml}
    `;
    if (!isFull) {
      div.addEventListener("click", () => addCardToDeck(name));
    }
    div.addEventListener("mouseenter", e => showPoolTooltip(e, name, card));
    div.addEventListener("mouseleave", () => hideTooltip("card-tooltip"));
    frag.appendChild(div);
  });
  pool.appendChild(frag);
}

function addCardToDeck(name) {
  if (draftDeck.length >= DECK_SIZE) return;
  const card = CARD_DB[name];
  if (!card || !cardAllowedForClass(card, selectedClass)) return;
  const maxCopies = CARD_DB[name]?.legendary ? 1 : 2;
  if (draftDeck.filter(c => c === name).length >= maxCopies) return;
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
  const countBox = document.querySelector(".deck-count-box");
  document.getElementById("deck-count").textContent    = count;
  document.getElementById("deck-progress").style.width = `${(count / DECK_SIZE) * 100}%`;
  if (countBox) countBox.classList.toggle("deck-count-box--ready", count === DECK_SIZE);

  const list   = document.getElementById("deck-list");
  list.innerHTML = "";
  const unique = [...new Set(draftDeck)].sort();
  unique.forEach(name => {
    const n    = draftDeck.filter(c => c === name).length;
    const cost = CARD_DB[name]?.cost ?? "?";
    const li   = document.createElement("li");
    li.className = "deck-entry";
    li.innerHTML = `<span class="deck-entry-cost">${cost}</span>
                    <span class="deck-entry-name">${name}</span>
                    <span class="deck-entry-count">x${n}</span>
                    <span class="deck-entry-remove" title="Remove">✕</span>`;
    li.querySelector(".deck-entry-remove").addEventListener("click", () => removeFromDeck(name));
    list.appendChild(li);
  });

  document.getElementById("btn-start-ai").disabled = count !== DECK_SIZE;
  const startBtn = document.getElementById("btn-start-ai");
  if (startBtn) {
    startBtn.textContent = count === DECK_SIZE ? "⚔️ Play vs AI" : `Need ${DECK_SIZE - count} cards`;
  }
  renderManaCurve();
  updateDeckValidation();
}

function renderManaCurve() {
  const curveEl = document.getElementById("mana-curve");
  if (!curveEl) return;

  const counts = {};
  for (let i = 1; i <= MANA_CURVE_MAX_COST; i++) counts[i] = 0;
  draftDeck.forEach(name => {
    const cost   = CARD_DB[name]?.cost ?? 0;
    const bucket = Math.min(cost, MANA_CURVE_MAX_COST);
    // Cards with cost 0 are excluded from the curve (none exist in the current DB)
    if (bucket > 0) counts[bucket] = (counts[bucket] || 0) + 1;
  });

  const maxCount = Math.max(...Object.values(counts), 1);
  curveEl.innerHTML = Object.entries(counts).map(([cost, count]) => {
    const pct   = Math.round((count / maxCount) * 100);
    const label = Number(cost) === MANA_CURVE_MAX_COST ? `${cost}+` : cost;
    return `<div class="curve-bar-wrap">
      <div class="curve-bar-inner">
        <div class="curve-bar" style="height:${pct}%" title="${count} card${count !== 1 ? "s" : ""}"></div>
      </div>
      <div class="curve-label">${label}</div>
    </div>`;
  }).join("");
}

function autoFillDeck() {
  const pool = poolCardNames();
  let tries = 0;
  while (draftDeck.length < DECK_SIZE && tries < MAX_AUTOFILL_ATTEMPTS) {
    tries++;
    const name = pool[Math.floor(Math.random() * pool.length)];
    const maxCopies = CARD_DB[name]?.legendary ? 1 : 2;
    if (draftDeck.filter(c => c === name).length < maxCopies) {
      draftDeck.push(name);
    }
  }
  renderCardPool();
  updateDeckSidebar();
}

function clearDeck() {
  draftDeck = [];
  renderCardPool();
  updateDeckSidebar();
}

// ---------------------------------------------------------------------------
// SAVE / LOAD DECKS  (localStorage)
// ---------------------------------------------------------------------------
function getSavedDecks() {
  try {
    return JSON.parse(localStorage.getItem("litstoneDecks") || "{}");
  } catch (_) {
    return {};
  }
}

function saveDeck() {
  const nameInput = document.getElementById("save-deck-name");
  const name = nameInput?.value.trim();
  if (!name || draftDeck.length === 0) return;
  const saved = getSavedDecks();
  saved[name] = { heroClass: selectedClass, cards: [...draftDeck] };
  localStorage.setItem("litstoneDecks", JSON.stringify(saved));
  nameInput.value = "";
  renderSavedDecks();
}

function loadDeck(name) {
  const saved = getSavedDecks();
  const entry = saved[name];
  if (!entry) return;
  if (entry.heroClass && entry.heroClass !== selectedClass) {
    showStatusToast(`That deck is for ${entry.heroClass} — pick that class first.`);
    return;
  }
  draftDeck = entry.cards.filter(c => CARD_DB[c] && cardAllowedForClass(CARD_DB[c], selectedClass));
  if (draftDeck.length !== DECK_SIZE) {
    showStatusToast(`Loaded ${draftDeck.length}/${DECK_SIZE} cards — fill the rest.`);
  } else {
    showStatusToast(`Loaded "${name}"`);
  }
  renderCardPool();
  updateDeckSidebar();
}

function deleteSavedDeck(name) {
  const saved = getSavedDecks();
  delete saved[name];
  localStorage.setItem("litstoneDecks", JSON.stringify(saved));
  renderSavedDecks();
}

function renderSavedDecks() {
  const el = document.getElementById("saved-decks-list");
  if (!el) return;
  const entries = Object.entries(getSavedDecks());
  if (entries.length === 0) {
    el.innerHTML = `<div class="saved-decks-empty">No saved decks</div>`;
    return;
  }
  el.innerHTML = "";
  entries
    .filter(([, data]) => !data.heroClass || data.heroClass === selectedClass)
    .forEach(([name, data]) => {
      const div = document.createElement("div");
      div.className = "saved-deck-entry";
      const count = data.cards?.length ?? 0;
      div.innerHTML = `
        <span class="saved-deck-name" title="${name}">${name}</span>
        <span class="saved-deck-class">${count}/${DECK_SIZE}</span>
        <button type="button" class="btn-load-deck">Load</button>
        <button type="button" class="btn-delete-deck" aria-label="Delete">✕</button>
      `;
      div.querySelector(".btn-load-deck").addEventListener("click", () => loadDeck(name));
      div.querySelector(".btn-delete-deck").addEventListener("click", () => deleteSavedDeck(name));
      el.appendChild(div);
    });
  if (el.children.length === 0) {
    el.innerHTML = `<div class="saved-decks-empty">No saved ${selectedClass} decks</div>`;
  }
}

// ---------------------------------------------------------------------------
// MULLIGAN
// ---------------------------------------------------------------------------
let mulliganSwapSet = new Set(); // indices of cards marked for swap

function renderMulligan(state) {
  const hand = state.p1.hand;
  mulliganSwapSet = new Set();
  const sub = document.querySelector(".mulligan-subtitle");
  if (sub) {
    const goingFirst = state.player_goes_first !== false;
    sub.textContent = goingFirst
      ? `You go first — ${hand.length} cards. Click to swap, then confirm.`
      : `You go second — ${hand.length} cards. You'll receive The Coin after mulligan.`;
  }
  const container = document.getElementById("mulligan-cards");
  container.innerHTML = "";

  hand.forEach((name, idx) => {
    const card = CARD_DB[name] || {};
    const div  = document.createElement("div");
    div.className = `mulligan-card marked-keep ${CardArt.frameClasses(card, name)}`;
    div.dataset.idx = idx;
    div.setAttribute("role", "button");
    div.setAttribute("tabindex", "0");
    div.setAttribute("aria-pressed", "false");
    div.setAttribute("aria-label", `${name}, ${mulliganSwapSet.has(idx) ? "swap" : "keep"}`);

    let statsHtml = "";
    if (card.type === "minion") {
      statsHtml = `<div class="mulligan-card-stats"><span class="atk">${card.atk}⚔</span><span class="hp">${card.hp}♥</span></div>`;
    } else if (card.type === "weapon") {
      statsHtml = `<div class="mulligan-card-stats"><span class="atk">${card.atk}⚔</span><span class="hp">${card.durability}🛡</span></div>`;
    } else {
      statsHtml = `<div class="mulligan-card-desc">${spellDesc(card, true)}</div>`;
    }

    div.innerHTML = `
      <div class="mulligan-card-cost">${card.cost}</div>
      ${CardArt.renderArt(card, name, "mulligan")}
      <div class="mulligan-card-name">${name}</div>
      <div class="mulligan-card-type">${card.type}</div>
      ${statsHtml}
    `;

    div.addEventListener("click", () => toggleMulliganCard(div, idx));
    div.addEventListener("keydown", e => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        toggleMulliganCard(div, idx);
      }
    });
    container.appendChild(div);
  });

  document.getElementById("btn-mulligan-confirm").textContent = "✓ Keep Hand";
  showScreen("screen-mulligan");
}

function toggleMulliganCard(el, idx) {
  const swapping = !mulliganSwapSet.has(idx);
  if (swapping) {
    mulliganSwapSet.add(idx);
    el.classList.remove("marked-keep");
    el.classList.add("marked-swap");
  } else {
    mulliganSwapSet.delete(idx);
    el.classList.remove("marked-swap");
    el.classList.add("marked-keep");
  }
  el.setAttribute("aria-pressed", swapping ? "true" : "false");
  const swapCount = mulliganSwapSet.size;
  const btn = document.getElementById("btn-mulligan-confirm");
  btn.textContent = swapCount > 0 ? `↺ Swap ${swapCount} Card${swapCount > 1 ? "s" : ""}` : "✓ Keep Hand";
}

async function confirmMulligan() {
  const indices = Array.from(mulliganSwapSet);
  const btn = document.getElementById("btn-mulligan-confirm");
  if (btn) btn.disabled = true;
  showLoading("Entering match…");
  try {
    const data = await apiFetch("/api/mulligan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ game_id: gameId, indices }),
    });
    lastMatchDeck = { heroClass: selectedClass, cards: [...draftDeck] };
    gameId           = data.game_id || gameId;
    CARD_DB          = data.card_db || CARD_DB;
    gameState        = data;
    syncNavigationFromGameState(data);
    selected         = null;
    prevIsPlayerTurn = null;
    turnNumber       = data.turn_number || 1;
    isActing         = false;
    initGameScreenUi();
    showScreen("screen-game");
    showTurnBanner(true);
    renderGame();
  } catch (err) {
    showStatusToast(err.message || "Network error during mulligan.");
    if (btn) btn.disabled = false;
  } finally {
    hideLoading();
  }
}

async function startGame() {
  if (draftDeck.length !== DECK_SIZE) return;
  saveLastDeck();
  lastMatchDeck = { heroClass: selectedClass, cards: [...draftDeck] };
  const startBtn = document.getElementById("btn-start-ai");
  if (startBtn) startBtn.disabled = true;
  const diffEl = document.getElementById("match-difficulty");
  const difficulty = diffEl?.value || "normal";
  const payload = {
    hero_class: selectedClass,
    deck: draftDeck,
    difficulty,
  };
  if (activeCampaignNode) payload.campaign_node = activeCampaignNode;
  if (tutorialActive) payload.tutorial = true;
  if (practiceActive) {
    payload.practice = true;
    payload.p1_hp = practiceOptions.p1_hp;
    payload.p2_hp = practiceOptions.p2_hp;
    payload.infinite_mana = practiceOptions.infinite_mana;
    payload.difficulty = "easy";
  }
  const loadMsg = activeCampaignNode
    ? "Starting encounter…"
    : (practiceActive ? "Opening practice sandbox…" : "Finding opponent…");
  showLoading(loadMsg);
  try {
    const data = await apiFetch("/api/new_game", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload),
    });
    gameId    = data.game_id || null;
    CARD_DB   = data.card_db;
    gameState = data;
    syncNavigationFromGameState(data);
    isActing  = false;
    if (data.mulligan_phase) {
      renderMulligan(data);
    } else {
      selected         = null;
      prevIsPlayerTurn = null;
      turnNumber       = data.turn_number || 1;
      initGameScreenUi();
      showScreen("screen-game");
      showTurnBanner(true);
      renderGame();
    }
  } catch (err) {
    showStatusToast(err.message || "Failed to start game. Check your connection and try again.");
  } finally {
    hideLoading();
    if (startBtn) startBtn.disabled = false;
    updateDeckSidebar();
  }
}

function goBack() {
  if (tutorialActive) {
    tutorialActive = false;
    tutorialStep = 0;
    goToHub();
    return;
  }
  if (practiceActive) {
    showScreen("screen-practice");
    return;
  }
  if (activeCampaignNode) {
    goToCampaign();
    return;
  }
  showScreen("screen-menu");
}

async function playAgain() {
  if (!lastMatchDeck?.cards?.length) return;
  const ctx = captureMatchContext();
  document.getElementById("winner-overlay")?.classList.add("hidden");
  await abandonGame({ preserveNavigation: true });
  applyMatchContext(ctx);
  enterDeckBuilder(lastMatchDeck.heroClass, lastMatchDeck.cards);
  await startGame();
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
  if (e === "coin")       return short ? "+1 Mana"             : `Gain 1 Mana Crystal this turn only.`;
  if (e === "damage")     return short ? `Deal ${v} Dmg`       : `Deal ${v} damage.`;
  if (e === "heal")       return short ? `Heal ${v} HP`        : `Restore ${v} HP.`;
  if (e === "draw")       return short ? `Draw ${v} Cards`     : `Draw ${v} cards.`;
  if (e === "damage_all") return short ? `AoE ${v} Dmg`        : `Deal ${v} dmg to all enemy minions.`;
  if (e === "buff")       return short ? `Buff +${v[0]}/+${v[1]}` : `Give a minion +${v[0]}/+${v[1]}.`;
  if (e === "buff_all")   return short ? `Buff All +${v[0]}/+${v[1]}` : `Give all friendly minions +${v[0]}/+${v[1]}.`;
  if (e === "heal_all")   return short ? `Heal All ${v} HP`   : `Restore ${v} HP to all friendly characters.`;
  if (e === "add_shield") return short ? `Add Shield`          : `Give a friendly minion Divine Shield.`;
  if (e === "silence")    return short ? `Silence`             : `Remove all text from an enemy minion.`;
  return "";
}

function battlecryDesc(bc) {
  if (!bc) return "";
  if (bc.effect === "heal_hero")  return `Battlecry: Restore ${bc.val} HP to your hero.`;
  if (bc.effect === "draw_cards") return `Battlecry: Draw ${bc.val} card${bc.val !== 1 ? "s" : ""}.`;
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
  const isLegendary = !!card.legendary;

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

  const legendaryBadge = isLegendary
    ? `<div class="tooltip-legendary">♦ LEGENDARY</div>` : "";
  const classBadge = card.classes?.length
    ? `<div class="tooltip-desc" style="color:var(--col-gold)">${card.classes.join(", ")} class</div>` : "";

  return `
    <div class="tooltip-art-wrap">${CardArt.renderArt(card, name, "tooltip")}</div>
    <div class="tooltip-name">${name}</div>
    <div class="tooltip-type">${card.type.toUpperCase()} · ${card.cost} Mana</div>
    ${legendaryBadge}
    ${classBadge}
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
  if (gameSpeed === "instant") return;
  const banner = document.getElementById("turn-banner");
  if (!banner) return;
  // Reset: remove active so re-triggering re-plays the animation
  banner.className = `turn-banner turn-banner--${isPlayerTurn ? "player" : "enemy"}`;
  banner.textContent = isPlayerTurn ? "YOUR TURN" : "ENEMY TURN";
  // Force reflow so animation restarts cleanly
  void banner.offsetWidth;
  banner.classList.add("active");
  playSfx("turn");
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
        // (e.g. Fairy Blessing gives +2/+2 — both changes should be visible)
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
  if (gameState.p1.hp < prev.p1.hp) {
    const dmg = prev.p1.hp - gameState.p1.hp;
    flashHero("hero-player");
    spawnFloat(`-${dmg}`, "var(--col-dmg)", document.getElementById("hero-player"), "big");
  } else if (gameState.p1.hp > prev.p1.hp) {
    const heal = gameState.p1.hp - prev.p1.hp;
    spawnFloat(`+${heal}♥`, "var(--col-heal)", document.getElementById("hero-player"), "normal");
  }
  const p1ArmorGain = (gameState.p1.armor || 0) - (prev.p1.armor || 0);
  if (p1ArmorGain > 0) {
    spawnFloat(`+${p1ArmorGain}🛡`, "var(--col-gold)", document.getElementById("hero-player"), "normal");
  }
  if (gameState.p2.hp < prev.p2.hp) {
    const dmg = prev.p2.hp - gameState.p2.hp;
    flashHero("hero-opp");
    spawnFloat(`-${dmg}`, "var(--col-dmg)", document.getElementById("hero-opp"), "big");
  } else if (gameState.p2.hp > prev.p2.hp) {
    const heal = gameState.p2.hp - prev.p2.hp;
    spawnFloat(`+${heal}♥`, "var(--col-heal)", document.getElementById("hero-opp"), "normal");
  }
  const p2ArmorGain = (gameState.p2.armor || 0) - (prev.p2.armor || 0);
  if (p2ArmorGain > 0) {
    spawnFloat(`+${p2ArmorGain}🛡`, "var(--col-gold)", document.getElementById("hero-opp"), "normal");
  }
  if (gameState.p1.hp < prev.p1.hp || gameState.p2.hp < prev.p2.hp) playSfx("damage");
  if (gameState.p1.hp > prev.p1.hp) playSfx("heal");
}

// ---------------------------------------------------------------------------
// SOUND FX (Web Audio — no asset files)
// ---------------------------------------------------------------------------

function motionEnabled() {
  if (gameSpeed === "instant") return false;
  if (!animationsEnabled) return false;
  return !window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

function getAudioCtx() {
  if (!audioCtx) {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  }
  return audioCtx;
}

function tone(freq, duration, type = "sine", volume = 0.07) {
  const ctx = getAudioCtx();
  const osc = ctx.createOscillator();
  const gain = ctx.createGain();
  osc.type = type;
  osc.frequency.value = freq;
  gain.gain.setValueAtTime(volume, ctx.currentTime);
  gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);
  osc.connect(gain);
  gain.connect(ctx.destination);
  osc.start(ctx.currentTime);
  osc.stop(ctx.currentTime + duration);
}

function playSfx(kind) {
  if (sfxMuted) return;
  try {
    const ctx = getAudioCtx();
    if (ctx.state === "suspended") ctx.resume();
    switch (kind) {
      case "play":
        tone(392, 0.1);
        setTimeout(() => tone(523, 0.12), 60);
        break;
      case "attack":
        tone(160, 0.14, "square", 0.05);
        break;
      case "damage":
        tone(110, 0.18, "sawtooth", 0.045);
        break;
      case "heal":
        tone(440, 0.14);
        setTimeout(() => tone(554, 0.16), 80);
        break;
      case "turn":
        tone(330, 0.2);
        setTimeout(() => tone(440, 0.15), 100);
        break;
      case "victory":
        tone(523, 0.18);
        setTimeout(() => tone(659, 0.18), 140);
        setTimeout(() => tone(784, 0.22), 280);
        break;
      case "defeat":
        tone(220, 0.25, "triangle", 0.06);
        setTimeout(() => tone(165, 0.35, "triangle", 0.05), 200);
        break;
      default:
        break;
    }
  } catch (_) {
    /* Audio unavailable */
  }
}

function toggleSfx() {
  sfxMuted = !sfxMuted;
  settings.sfx = !sfxMuted;
  saveSettings();
  const btn = document.getElementById("btn-sfx-toggle");
  if (btn) {
    btn.textContent = sfxMuted ? "🔇" : "🔊";
    btn.title = sfxMuted ? "Unmute sound" : "Mute sound";
    btn.setAttribute("aria-pressed", sfxMuted ? "true" : "false");
  }
  if (!sfxMuted) playSfx("turn");
}

function syncSfxButton() {
  const btn = document.getElementById("btn-sfx-toggle");
  if (!btn) return;
  btn.textContent = sfxMuted ? "🔇" : "🔊";
  btn.title = sfxMuted ? "Unmute sound" : "Mute sound";
  btn.setAttribute("aria-pressed", sfxMuted ? "true" : "false");
}

// ---------------------------------------------------------------------------
// ACTION ANIMATIONS (play arc, attack lunge, death burst)
// ---------------------------------------------------------------------------

function snapshotBoardRects() {
  function grab(boardId) {
    const board = document.getElementById(boardId);
    if (!board) return [];
    return Array.from(board.querySelectorAll(".minion-card")).map(el => ({
      name: el.querySelector(".minion-name")?.textContent || "",
      rect: el.getBoundingClientRect(),
    }));
  }
  return { p1: grab("board-player"), p2: grab("board-opp") };
}

function snapshotHandRects() {
  const hand = document.getElementById("hand-player");
  if (!hand) return [];
  return Array.from(hand.querySelectorAll(".hand-card")).map(el => ({
    name: el.querySelector(".minion-name")?.textContent || "",
    rect: el.getBoundingClientRect(),
  }));
}

function countMinionsByName(board) {
  const counts = {};
  board.forEach(m => { counts[m.name] = (counts[m.name] || 0) + 1; });
  return counts;
}

function minionsLost(prevBoard, currBoard) {
  const prevC = countMinionsByName(prevBoard);
  const currC = countMinionsByName(currBoard);
  const lost = [];
  Object.keys(prevC).forEach(name => {
    const diff = prevC[name] - (currC[name] || 0);
    for (let i = 0; i < diff; i++) lost.push(name);
  });
  return lost;
}

function consumeRectForName(rects, name) {
  const idx = rects.findIndex(r => r.name === name);
  if (idx === -1) return null;
  return rects.splice(idx, 1)[0].rect;
}

function findMinionEl(boardId, name) {
  const board = document.getElementById(boardId);
  if (!board) return null;
  for (const el of board.querySelectorAll(".minion-card")) {
    if (el.querySelector(".minion-name")?.textContent === name) return el;
  }
  return null;
}

function findHeroElByName(name) {
  if (name === "Player") return document.getElementById("hero-player");
  if (name === "AI") return document.getElementById("hero-opp");
  return null;
}

function animateFlyGhost(fromRect, toRect, card, name) {
  if (!motionEnabled() || !fromRect || !toRect) return;
  const layer = document.getElementById("fx-layer");
  if (!layer) return;
  const layerRect = layer.getBoundingClientRect();
  const el = document.createElement("div");
  el.innerHTML = CardArt.renderFlyCard(card || {}, name);
  const fly = el.firstElementChild;
  if (!fly) return;

  const sx = fromRect.left + fromRect.width / 2 - layerRect.left;
  const sy = fromRect.top + fromRect.height / 2 - layerRect.top;
  fly.style.left = `${sx}px`;
  fly.style.top  = `${sy}px`;
  layer.appendChild(fly);

  const dx = toRect.left + toRect.width / 2 - layerRect.left - sx;
  const dy = toRect.top + toRect.height / 2 - layerRect.top - sy;

  const flyDur = animMs(380);
  if (flyDur <= 0) {
    fly.remove();
    return;
  }
  fly.animate([
    { transform: "translate(-50%, -50%) scale(1.15) rotate(-6deg)", opacity: 1 },
    { transform: `translate(calc(-50% + ${dx * 0.45}px), calc(-50% + ${dy * 0.25}px)) scale(1) rotate(2deg)`, opacity: 1, offset: 0.55 },
    { transform: `translate(calc(-50% + ${dx}px), calc(-50% + ${dy}px)) scale(0.75) rotate(0deg)`, opacity: 0 },
  ], { duration: flyDur, easing: "cubic-bezier(.25, .8, .25, 1)", fill: "forwards" })
    .addEventListener("finish", () => fly.remove());
}

function animateDeathBurst(rect) {
  if (!motionEnabled() || !rect) return;
  const layer = document.getElementById("fx-layer");
  if (!layer) return;
  const layerRect = layer.getBoundingClientRect();
  const cx = rect.left + rect.width / 2 - layerRect.left;
  const cy = rect.top + rect.height / 2 - layerRect.top;

  for (let i = 0; i < 6; i++) {
    const shard = document.createElement("div");
    shard.className = "fx-death-shard";
    shard.style.left = `${cx}px`;
    shard.style.top = `${cy}px`;
    const angle = (i / 6) * Math.PI * 2;
    const dist = 28 + Math.random() * 22;
    layer.appendChild(shard);
    shard.animate([
      { transform: "translate(-50%, -50%) scale(1)", opacity: 1 },
      { transform: `translate(calc(-50% + ${Math.cos(angle) * dist}px), calc(-50% + ${Math.sin(angle) * dist}px)) scale(0.2)`, opacity: 0 },
    ], { duration: 420, easing: "ease-out", fill: "forwards" })
      .addEventListener("finish", () => shard.remove());
  }
}

function animateLunge(attackerEl, targetEl, fromPlayerBoard) {
  if (!motionEnabled() || !attackerEl) return;
  const cls = fromPlayerBoard ? "attack-lunge" : "attack-lunge-opp";
  attackerEl.classList.remove(cls);
  void attackerEl.offsetWidth;
  attackerEl.classList.add(cls);
  attackerEl.addEventListener("animationend", () => attackerEl.classList.remove(cls), { once: true });
  if (targetEl) {
    targetEl.classList.add("damage-flash");
    targetEl.addEventListener("animationend", () => targetEl.classList.remove("damage-flash"), { once: true });
  }
}

function animateHeroWeaponSwing(heroEl, targetEl, isPlayerHero) {
  if (!motionEnabled() || !heroEl) return;
  heroEl.classList.add(isPlayerHero ? "hero-weapon-swing" : "hero-weapon-swing-opp");
  heroEl.addEventListener("animationend", () => {
    heroEl.classList.remove("hero-weapon-swing", "hero-weapon-swing-opp");
  }, { once: true });
  if (targetEl) {
    targetEl.classList.add("damage-flash");
    targetEl.addEventListener("animationend", () => targetEl.classList.remove("damage-flash"), { once: true });
  }
}

function flashSpellBoard(boardId) {
  const board = document.getElementById(boardId);
  if (!board || !motionEnabled()) return;
  const flash = document.createElement("div");
  flash.className = "board-spell-flash";
  board.style.position = "relative";
  board.appendChild(flash);
  flash.addEventListener("animationend", () => flash.remove());
}

function parseLogAttacks(log, fromIndex) {
  const attacks = [];
  (log || []).slice(fromIndex).forEach(line => {
    const m = line.match(/^>> (.+?) attacks (.+?)(?: for | with )/);
    if (m) attacks.push({ attacker: m[1], target: m[2] });
  });
  return attacks;
}

function resolveAttackTarget(targetName) {
  const hero = findHeroElByName(targetName);
  if (hero) return { el: hero, isHero: true };
  const onPlayer = findMinionEl("board-player", targetName);
  if (onPlayer) return { el: onPlayer, isHero: false, onPlayerBoard: true };
  const onOpp = findMinionEl("board-opp", targetName);
  if (onOpp) return { el: onOpp, isHero: false, onPlayerBoard: false };
  return null;
}

function resolveAttacker(attackerName) {
  const onPlayer = findMinionEl("board-player", attackerName);
  if (onPlayer) return { el: onPlayer, fromPlayerBoard: true, isHero: false };
  const onOpp = findMinionEl("board-opp", attackerName);
  if (onOpp) return { el: onOpp, fromPlayerBoard: false, isHero: false };
  if (attackerName === "Player") return { el: document.getElementById("hero-player"), fromPlayerBoard: true, isHero: true };
  if (attackerName === "AI") return { el: document.getElementById("hero-opp"), fromPlayerBoard: false, isHero: true };
  return null;
}

function animateAttackPair(attackerName, targetName) {
  const atk = resolveAttacker(attackerName);
  const tgt = resolveAttackTarget(targetName);
  if (!atk?.el || !tgt?.el) return;
  playSfx("attack");
  if (atk.isHero) {
    animateHeroWeaponSwing(atk.el, tgt.el, atk.fromPlayerBoard);
  } else {
    animateLunge(atk.el, tgt.el, atk.fromPlayerBoard);
  }
}

function applyHandDrawAnimation(prevHandLen) {
  if (!gameState || gameState.p1.hand.length <= prevHandLen) return;
  const hand = document.getElementById("hand-player");
  if (!hand) return;
  const cards = hand.querySelectorAll(".hand-card");
  const newest = cards[cards.length - 1];
  if (!newest) return;
  newest.classList.add("card-draw-anim");
  newest.addEventListener("animationend", () => newest.classList.remove("card-draw-anim"), { once: true });
}

/**
 * Orchestrate play / attack / death animations after a state update.
 * @param {object} ctx - snapshots captured before the server round-trip
 */
function applyActionAnimations(ctx) {
  if (!ctx || !gameState) return;

  const motion = motionEnabled();
  const { prevSnap, prevRects, prevHandRects, action, idx, target, logFrom, prevHandLen, playedCardName } = ctx;
  const p1Rects = [...(prevRects?.p1 || [])];
  const p2Rects = [...(prevRects?.p2 || [])];

  if (motion) {
    minionsLost(prevSnap.p2, gameState.p2.board).forEach(name => {
      animateDeathBurst(consumeRectForName(p2Rects, name));
    });
    minionsLost(prevSnap.p1, gameState.p1.board).forEach(name => {
      animateDeathBurst(consumeRectForName(p1Rects, name));
    });
  }

  if (action === "play" && playedCardName) {
    const card = CARD_DB[playedCardName] || {};
    const handRect = prevHandRects?.[idx]?.rect;
    if (card.type === "minion") {
      const played = findMinionEl("board-player", playedCardName);
      if (motion && handRect && played) {
        animateFlyGhost(handRect, played.getBoundingClientRect(), card, playedCardName);
      }
      playSfx("play");
    } else if (card.type === "spell") {
      if (motion) {
        flashSpellBoard(card.effect === "damage_all" || card.effect === "silence" ? "board-opp" : "board-player");
      }
      playSfx("play");
    } else if (card.type === "weapon") {
      playSfx("play");
    }
  }

  if (action === "attack" && prevSnap?.p1?.[idx]) {
    const atkName = prevSnap.p1[idx].name;
    let tgtName = "AI";
    if (target !== "hero" && typeof target === "number" && prevSnap.p2[target]) {
      tgtName = prevSnap.p2[target].name;
    }
    if (motion) animateAttackPair(atkName, tgtName);
    else playSfx("attack");
  }

  if (action === "hero_attack") {
    let tgtName = "AI";
    if (target !== "hero" && typeof target === "number" && prevSnap?.p2?.[target]) {
      tgtName = prevSnap.p2[target].name;
    }
    playSfx("attack");
    if (motion) {
      animateHeroWeaponSwing(
        document.getElementById("hero-player"),
        resolveAttackTarget(tgtName)?.el,
        true
      );
    }
  }

  if (action === "end_turn" || !action) {
    const stagger = aiAttackStaggerMs();
    const attacks = parseLogAttacks(gameState.log, logFrom);
    if (stagger === 0) {
      if (motion) attacks.forEach(({ attacker, target: tgt }) => animateAttackPair(attacker, tgt));
      else if (attacks.length) playSfx("attack");
    } else {
      attacks.forEach(({ attacker, target: tgt }, i) => {
        setTimeout(() => {
          if (motion) animateAttackPair(attacker, tgt);
          else playSfx("attack");
        }, i * stagger);
      });
    }
  }

  if (motion) applyHandDrawAnimation(prevHandLen ?? 0);
}

function buildAnimContext(action, idx, target) {
  return {
    action,
    idx,
    target,
    prevSnap: snapshotBoards(),
    prevRects: snapshotBoardRects(),
    prevHandRects: snapshotHandRects(),
    prevHandLen: gameState?.p1?.hand?.length ?? 0,
    logFrom: gameState?.log?.length ?? 0,
    playedCardName: (action === "play" && idx != null) ? gameState?.p1?.hand?.[idx] : null,
    prevHeroSnap: {
      p1: { hp: gameState.p1.hp, armor: gameState.p1.armor || 0 },
      p2: { hp: gameState.p2.hp, armor: gameState.p2.armor || 0 },
    },
  };
}

function onGameStateUpdated(data, animCtx) {
  gameId    = data.game_id || gameId;
  CARD_DB   = data.card_db || CARD_DB;
  gameState = data;
  advanceTutorialFromState();
  renderGame();
  if (animCtx) {
    applyActionAnimations(animCtx);
    applyPostRenderAnimations(animCtx.prevSnap);
    applyHeroAnimations(animCtx.prevHeroSnap);
  }
  if (data.winner === "Player") onCampaignVictory();
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
  renderManaHud(p1);
  updateGameHelpBar();

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
    const isWin = winner === "Player";
    document.getElementById("winner-text").textContent =
      winner === "DRAW" ? "It's a Draw!" : isWin ? "Victory!" : "Defeat!";
    if (!overlay.dataset.sfxPlayed) {
      playSfx(winner === "DRAW" ? "turn" : isWin ? "victory" : "defeat");
      overlay.dataset.sfxPlayed = "1";
    }
  } else {
    overlay.classList.add("hidden");
    delete overlay.dataset.sfxPlayed;
  }

  updateSelectionInfo();
}

/* ---- Hero panel ---- */
function renderHero(elId, player, isOpp) {
  const el = document.getElementById(elId);

  const maxHp = player.max_hp || 30;
  const hpPct = Math.max(0, Math.min(100, (player.hp / maxHp) * 100));
  const icon  = HERO_ICONS[player.hero_class] || "?";
  const accentColor = HERO_COLORS[player.hero_class] || "#2e4a66";

  let cls = "hero-panel";
  if (!isOpp) {
    const canAtk = player.weapon && player.hero_can_attack;
    if (canAtk && !selected) cls += " attackable";
    if (selected?.type === "hero_weapon") cls += " selected";
  }

  if (selected && isValidHeroTarget(isOpp)) cls += " valid-target";
  if (player.hp <= Math.max(10, Math.floor(maxHp * 0.33))) cls += " low-hp";

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
    if (card?.effect === "add_shield") return false;
    if (card?.effect === "silence") return false;  // silence targets minions only
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
    if (["buff", "add_shield"].includes(card?.effect) &&  isOpp) return false;
    if (card?.effect === "damage" && !isOpp) return false;
    if (card?.effect === "silence" && !isOpp) return false;  // silence targets enemy minions
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
  const icon   = HERO_POWER_ICONS[player.hero_class] || "⚡";

  let cls = "hero-power-panel";
  if (!canUse) cls += " used";
  if (!isOpp && selected?.type === "hero_power") cls += " selected";

  el.className = cls;
  el.dataset.class = player.hero_class;
  el.innerHTML = `<div class="hp-icon">${icon}</div><div class="hp-cost">${HERO_POWER_LABELS[player.hero_class] || "Power"}<br>2 Mana</div>`;

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

    let cls = `minion-card ${CardArt.frameClasses(card, minion.name)}`;
    if (!isOpp && minion.can_attack && !selected)                      cls += " can-attack";
    if (!isOpp && selected?.type === "board" && selected.idx === idx)  cls += " selected";
    if (minion.taunt)                                                   cls += " taunt";
    if (minion.divine_shield)                                           cls += " divine-shield";
    if (!minion.can_attack && !isOpp)                                   cls += " exhausted";
    if (card.legendary)                                                 cls += " legendary";

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
      ${CardArt.renderArt(card, minion.name, "board")}
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

    let cls = `hand-card hand-card--${card.type} ${CardArt.frameClasses(card, name)}`;
    if (!affordable)                                       cls += " unaffordable";
    if (selected?.type === "hand" && selected.idx === idx) cls += " selected";
    if (card.legendary)                                    cls += " legendary";
    if (name === "The Coin" || card.effect === "coin")     cls += " hand-card--coin";

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
      ${CardArt.renderArt(card, name, "hand")}
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
function logEntryClass(msg) {
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
  return cls;
}

function renderLog(entries) {
  const el = document.getElementById("log-entries");
  if (!el) return;
  const slice = entries.slice(-60);
  const wasAtBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 30;

  if (slice.length < logRenderedCount) {
    el.innerHTML = "";
    logRenderedCount = 0;
  }

  const frag = document.createDocumentFragment();
  slice.slice(logRenderedCount).forEach(msg => {
    const div = document.createElement("div");
    div.className = logEntryClass(msg);
    div.textContent = msg;
    frag.appendChild(div);
  });
  logRenderedCount = slice.length;
  el.appendChild(frag);
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
  const help = document.getElementById("game-help-bar");
  if (!selected) {
    el.classList.add("hidden");
    if (help) help.classList.remove("hidden");
    return;
  }
  el.classList.remove("hidden");
  if (help) help.classList.add("hidden");
  let msg = "";
  if (selected.type === "hand") {
    const card = CARD_DB[gameState.p1.hand[selected.idx]] || {};
    const needsTarget = ["damage", "buff", "add_shield", "silence"].includes(card.effect);
    msg = needsTarget
      ? `Target for ${gameState.p1.hand[selected.idx]} — click a highlighted target (Esc to cancel)`
      : `Confirm ${gameState.p1.hand[selected.idx]} — click again to cancel`;
  }
  if (selected.type === "board") {
    msg = `Attacking with ${gameState.p1.board[selected.idx].name} — click enemy or minion`;
  }
  if (selected.type === "hero_power")  msg = "Hero Power — click a valid target";
  if (selected.type === "hero_weapon") msg = "Hero attack — click a valid target";
  el.textContent = msg;
}

function getLegalMoves() {
  return gameState?._legal_moves || null;
}

// ---------------------------------------------------------------------------
// CLICK HANDLERS
// ---------------------------------------------------------------------------
function handleHandClick(idx, p1, name, card, affordable) {
  if (isPaused || !gameState.is_player_turn || gameState.winner) return;
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
    const handEl  = document.getElementById("hand-player");
    const cardEls = handEl ? handEl.querySelectorAll(".hand-card") : [];
    if (p1.board.length >= 7) {
      spawnFloat("Board is full!", "var(--col-red)", cardEls[idx] || null, "small");
      shakeElement(cardEls[idx]);
      return;
    }
    sendAction("play", idx, null);
    return;
  }
  if (card.type === "weapon") {
    sendAction("play", idx, null);
    return;
  }
  if (card.type === "spell") {
    if (["heal", "draw", "damage_all", "buff_all", "heal_all", "coin"].includes(card.effect)) {
      sendAction("play", idx, null);
      return;
    }
    if (["buff", "add_shield"].includes(card.effect) && p1.board.length === 0) {
      const handEl  = document.getElementById("hand-player");
      const cardEls = handEl ? handEl.querySelectorAll(".hand-card") : [];
      spawnFloat("No friendly minions!", "var(--col-red)", cardEls[idx] || null, "small");
      shakeElement(cardEls[idx]);
      return;
    }
    if (card.effect === "silence" && gameState.p2.board.length === 0) {
      const handEl  = document.getElementById("hand-player");
      const cardEls = handEl ? handEl.querySelectorAll(".hand-card") : [];
      spawnFloat("No enemy minions!", "var(--col-red)", cardEls[idx] || null, "small");
      shakeElement(cardEls[idx]);
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
  if (isPaused || !gameState.is_player_turn || gameState.winner) return;

  if (selected) {
    const targetValid = isValidMinionTarget(idx, isOpp);
    if (!targetValid) {
      const boardEl = document.getElementById(isOpp ? "board-opp" : "board-player");
      const cards   = boardEl ? boardEl.querySelectorAll(".minion-card") : [];
      spawnFloat("Invalid target!", "var(--col-red)", cards[idx] || null, "small");
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
    return;
  }

  // Clicking an enemy minion with nothing selected: hint the player
  if (isOpp && !selected) {
    const boardEl = document.getElementById("board-opp");
    const cards   = boardEl ? boardEl.querySelectorAll(".minion-card") : [];
    spawnFloat("Select your attacker first!", "var(--col-gold)", cards[idx] || null, "small");
  }
}

function handleHeroClick(isOpp, player) {
  if (isPaused || !gameState.is_player_turn || gameState.winner) return;

  if (selected) {
    if (!isValidHeroTarget(isOpp)) {
      const heroEl = document.getElementById(isOpp ? "hero-opp" : "hero-player");
      spawnFloat("Invalid target!", "var(--col-red)", heroEl, "small");
      shakeElement(heroEl);
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
  if (isPaused || !gameState.is_player_turn || gameState.winner) return;
  if (!canUse) {
    const msg = player.hero_power_used ? "Already used!" : "Not enough mana!";
    spawnFloat(msg, "var(--col-purple-bright)", null, "small");
    return;
  }

  if (selected?.type === "hero_power") { clearSelection(); return; }
  clearSelection();

  if (["Warrior", "Rogue", "Paladin", "Shaman"].includes(player.hero_class)) {
    sendAction("hero_power", null, null); return;
  }
  selected = { type: "hero_power" };
  renderGame();
}

document.addEventListener("keydown", e => {
  if (e.key !== "Escape") return;
  const settingsOpen = !document.getElementById("settings-modal")?.classList.contains("hidden");
  const pauseOpen = !document.getElementById("pause-overlay")?.classList.contains("hidden");
  if (settingsOpen) {
    closeSettings();
    return;
  }
  if (pauseOpen) {
    closePause();
    return;
  }
  if (document.getElementById("screen-game")?.classList.contains("active") && gameState && !gameState.winner) {
    if (selected) {
      clearSelection();
      return;
    }
    openPause();
    return;
  }
  if (selected) clearSelection();
});
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

let resizeUiTimer;
window.addEventListener("resize", () => {
  clearTimeout(resizeUiTimer);
  resizeUiTimer = setTimeout(() => {
    if (!document.getElementById("screen-game")?.classList.contains("active")) return;
    if (isNarrowViewport() && combatLogOpen) {
      combatLogOpen = false;
      applyCombatLogState();
    }
  }, 150);
});

// ---------------------------------------------------------------------------
// API CALLS
// ---------------------------------------------------------------------------
async function sendAction(action, idx, target) {
  if (isPaused || isActing || !gameState?.is_player_turn) return;
  isActing = true;

  const etBtn = document.getElementById("btn-end-turn");
  etBtn.disabled = true;

  const animCtx = buildAnimContext(action, idx, target);

  try {
    const data = await apiFetch("/api/action", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ game_id: gameId, action, idx, target }),
    });
    onGameStateUpdated(data, animCtx);
  } catch (err) {
    spawnFloat(err.message || "Network error!", "var(--col-red)", null, "normal");
  } finally {
    isActing = false;
    if (gameState?.is_player_turn && !gameState?.winner) etBtn.disabled = false;
  }
}

async function endTurn() {
  if (isPaused || isActing || !gameState?.is_player_turn) return;
  isActing = true;
  clearSelection();

  const etBtn = document.getElementById("btn-end-turn");
  etBtn.disabled = true;
  setAiThinking(true);

  const animCtx = buildAnimContext("end_turn", null, null);

  try {
    const data = await apiFetch("/api/action", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ game_id: gameId, action: "end_turn", idx: null, target: null }),
    });
    // Guard: player may have resigned while the AI was thinking
    if (gameState === null) return;
    setAiThinking(false);
    if (!data.winner) turnNumber = data.turn_number || (turnNumber + 1);
    onGameStateUpdated(data, animCtx);
    if (!gameState.winner) showTurnBanner(true);
  } catch (err) {
    spawnFloat(err.message || "Network error!", "var(--col-red)", null, "normal");
    setAiThinking(false);
    etBtn.textContent = "End Turn";
    etBtn.disabled = false;
  } finally {
    isActing = false;
  }
}

async function abandonGame(options = {}) {
  closePause(false);
  if (!options.preserveNavigation) {
    activeCampaignNode = null;
    tutorialActive = false;
    practiceActive = false;
  }
  try {
    if (gameId) {
      await fetch("/api/resign", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ game_id: gameId }),
      });
    }
  } catch (_) {
    // Best-effort — local UI should still reset even if the server is unreachable.
  }
  resetGameState();
}

function resign() {
  if (settings.confirmResign && !confirm("Resign and return to menu?")) return;
  abandonGame().then(() => goToHub());
}

function returnToMenu() {
  abandonGame().then(() => goToHub());
}

function resetGameState() {
  gameId           = null;
  gameState        = null;
  selected         = null;
  prevIsPlayerTurn = null;
  turnNumber       = 0;
  isActing         = false;
  mulliganSwapSet  = new Set();
  logRenderedCount = 0;
  tutorialStep     = 0;
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
function syncDeckSizeUi() {
  const maxEl = document.getElementById("deck-size-max");
  if (maxEl) maxEl.textContent = String(DECK_SIZE);
  const sub = document.querySelector(".deck-subtitle");
  if (sub) {
    sub.textContent = `Click cards to add · Maximum 2 copies · ${DECK_SIZE} cards total`;
  }
}

(async function init() {
  if (typeof NProgress !== "undefined") {
    NProgress.configure({ showSpinner: false, trickleSpeed: 120 });
  }

  let cardCount = 109;
  try {
    const res  = await fetch("/api/cards");
    const data = await res.json();
    if (data.card_db) CARD_DB = data.card_db;
    if (data.deck_size) DECK_SIZE = data.deck_size;
    cardCount = Object.keys(data.card_db || {}).filter(k => !data.card_db[k].uncollectible).length;
    syncDeckSizeUi();
  } catch (_) {}

  syncSfxButton();
  syncSettingsUi();
  applyGameSpeedClass();
  updateHubContinue();
  const meta = document.getElementById("hub-meta");
  if (meta) meta.textContent = `6 classes · ${cardCount} cards · campaign & tutorial`;
  if (localStorage.getItem(TUTORIAL_DONE_KEY) === "1") {
    const tbtn = document.getElementById("btn-hub-tutorial");
    if (tbtn) tbtn.textContent = "Tutorial ✓";
  }
  showScreen("screen-hub");
})();

document.getElementById("settings-modal")?.addEventListener("click", e => {
  if (e.target.id === "settings-modal") closeSettings();
});
