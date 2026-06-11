/* ============================================================
   LitStone — Procedural card art & frame helpers
   CSS-driven illustrated frames (no external image assets).
   ============================================================ */

"use strict";

const CLASS_ART = {
  Mage:    { accent: "#4a9edd", bg1: "#081830", bg2: "#143060", motif: "arcane" },
  Warrior: { accent: "#e05040", bg1: "#280808", bg2: "#501818", motif: "iron" },
  Priest:  { accent: "#f0b040", bg1: "#302008", bg2: "#504018", motif: "holy" },
  Rogue:   { accent: "#2ec4a8", bg1: "#082820", bg2: "#104038", motif: "shadow" },
  Paladin: { accent: "#e8c040", bg1: "#302808", bg2: "#504820", motif: "holy" },
  Shaman:  { accent: "#40c8f0", bg1: "#082830", bg2: "#104858", motif: "storm" },
};

const TYPE_ART = {
  minion: { accent: "#8ab0d0", bg1: "#0c1830", bg2: "#1a3050", motif: "creature" },
  spell:  { accent: "#c090f0", bg1: "#180828", bg2: "#301050", motif: "arcane" },
  weapon: { accent: "#e0a050", bg1: "#281408", bg2: "#403018", motif: "steel" },
};

const NEUTRAL_VARIANTS = [
  { hue: 205, accent: "#4a9edd" },
  { hue: 28,  accent: "#e8a040" },
  { hue: 340, accent: "#e06080" },
  { hue: 160, accent: "#40c8a0" },
  { hue: 270, accent: "#a080e0" },
  { hue: 45,  accent: "#d0a050" },
  { hue: 190, accent: "#50b8c8" },
  { hue: 15,  accent: "#c87050" },
  { hue: 120, accent: "#70c060" },
  { hue: 300, accent: "#d070d0" },
  { hue: 220, accent: "#6080e0" },
  { hue: 350, accent: "#e04060" },
];

const CARD_EMOJIS = {
  TC:"📯", CG:"🛡️", HW:"🤺", EK:"⚔️", TP:"🏰", SD:"🐉",
  CS:"🕷️", CC:"🙏", TA:"⚗️", QB:"✒️", IV:"🔥", HY:"🎶",
  DC:"🔍", RA:"🎯", FB:"✨", HB:"🗡️",
  LW:"📖", NV:"🪶", EL:"🧪", RL:"🚩", CM:"💚", EN:"🔰", IB:"🖋️", TS:"🤫",
  IH:"🏇", QS:"🔔", DQ:"🌀", SR:"⚔️",
  SH:"🕵️", JW:"🩺", PM:"♟️", VH:"🏹", VF:"🔬", FM:"🧟", AL:"🗝️", MH:"🎩",
  RB:"🐇", QH:"♥️", CH:"😼", SW:"🍎", RP:"🧵", SB:"😴", LR:"🧺", RU:"🪙",
  BW:"🐺", PP:"🎶", BY:"🧹", BB:"🔑", KA:"⚔️", ME:"🔮", LT:"🛡️", GV:"🌹",
  MF:"🧙‍♀️", MD:"🩸", GW:"🛡️", RH:"🏹", MM:"🌿", FT:"🍺", LJ:"💪", WS:"🎯",
  ES:"💰", OT:"🥣",
  CN:"🪙",
  NP:"🔥", EA:"📚", MK:"🪞", SK:"✨", SN:"🌋", AX:"📖", AM:"💨", MT:"☄️",
  BK:"🛡️", WG:"🏰", RR:"⚔️", BZ:"🪓", IA:"🔨", WD:"🥁", CV:"⚔️", FY:"🧱",
  HA:"🙏", BI:"📿", RC:"💫", CP:"⛪", SS:"💧", SM:"⚡", HH:"🎵", GR:"💖",
  BA:"🥷", SC:"👤", VV:"🐍", TV:"🔪", AR:"🗡️", KT:"💉", SV:"🌪️", HL:"💰",
  SL:"✝️", DK:"🌅", CR:"🏇", TU:"🗡️", HS:"📜", KD:"👑", PS:"☀️", LH:"🤲",
  WL:"🐺", TN:"🗿", FK:"🔥", HM:"🔱", LL:"⚡", MV:"🌊", HX:"🧿", AN:"👻",
  ST:"🔥", HE:"💚", SF:"🪨", WA:"💨",
};

function hashStr(s) {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = ((h << 5) - h + s.charCodeAt(i)) | 0;
  return Math.abs(h);
}

function emoji(icon) {
  return CARD_EMOJIS[icon] || icon || "?";
}

function isCoin(card, name) {
  return card?.effect === "coin" || name === "The Coin";
}

function resolveTheme(card) {
  const type = card?.type || "minion";
  if (isCoin(card)) {
    return { accent: "#ffd060", bg1: "#503800", bg2: "#806010", motif: "coin", variant: 0 };
  }
  if (card?.classes?.length && CLASS_ART[card.classes[0]]) {
    const base = CLASS_ART[card.classes[0]];
    const variant = hashStr(card.icon || type) % NEUTRAL_VARIANTS.length;
    return { ...base, variant };
  }
  const variant = hashStr(card?.icon || type) % NEUTRAL_VARIANTS.length;
  const neutral = NEUTRAL_VARIANTS[variant];
  const typeBase = TYPE_ART[type] || TYPE_ART.minion;
  return {
    accent: neutral.accent,
    bg1: typeBase.bg1,
    bg2: typeBase.bg2,
    motif: card?.legendary ? "legendary" : typeBase.motif,
    variant,
    hue: neutral.hue,
  };
}

function frameClasses(card, name, extra) {
  const type = card?.type || "minion";
  const parts = [`card-frame--${type}`];
  if (card?.legendary) parts.push("card-frame--legendary");
  if (card?.classes?.length) parts.push(`card-frame--class-${card.classes[0].toLowerCase()}`);
  if (isCoin(card, name)) parts.push("card-frame--coin");
  if (extra) parts.push(extra);
  return parts.join(" ");
}

function artStyle(card) {
  const t = resolveTheme(card);
  const style = {
    "--art-accent": t.accent,
    "--art-bg1": t.bg1,
    "--art-bg2": t.bg2,
  };
  if (t.hue != null) style["--art-hue"] = String(t.hue);
  return style;
}

function styleAttr(card) {
  const style = artStyle(card);
  return Object.entries(style).map(([k, v]) => `${k}:${v}`).join(";");
}

function applyArtVars(el, card) {
  if (!el) return;
  const t = resolveTheme(card);
  el.style.setProperty("--art-accent", t.accent);
  el.style.setProperty("--art-bg1", t.bg1);
  el.style.setProperty("--art-bg2", t.bg2);
  if (t.hue != null) el.style.setProperty("--art-hue", String(t.hue));
  el.dataset.motif = t.motif;
  el.dataset.variant = String(t.variant ?? 0);
  if (card?.classes?.[0]) el.dataset.cardClass = card.classes[0];
}

function renderArt(card, name, size) {
  const t = resolveTheme(card);
  const glyph = emoji(card?.icon);
  const sizeCls = size ? ` card-art--${size}` : "";
  const legCls = card?.legendary ? " card-art--legendary" : "";
  const coinCls = isCoin(card, name) ? " card-art--coin" : "";
  const classAttr = card?.classes?.[0] ? ` data-card-class="${card.classes[0]}"` : "";
  return `<div class="card-art${sizeCls}${legCls}${coinCls}" data-motif="${t.motif}" data-variant="${t.variant ?? 0}"${classAttr} style="${styleAttr(card)}">
    <div class="card-art__rim" aria-hidden="true"></div>
    <div class="card-art__bg" aria-hidden="true"></div>
    <div class="card-art__motif" aria-hidden="true"></div>
    <div class="card-art__vignette" aria-hidden="true"></div>
    <div class="card-art__shine" aria-hidden="true"></div>
    <span class="card-art__glyph" role="img" aria-label="">${glyph}</span>
  </div>`;
}

function renderFlyCard(card, name) {
  const fc = frameClasses(card, name, "fx-fly-card");
  return `<div class="fx-fly-card ${fc}" style="${styleAttr(card)}">
    ${renderArt(card, name, "fly")}
  </div>`;
}

const CardArt = {
  EMOJIS: CARD_EMOJIS,
  emoji,
  resolveTheme,
  frameClasses,
  artStyle,
  styleAttr,
  applyArtVars,
  renderArt,
  renderFlyCard,
};
