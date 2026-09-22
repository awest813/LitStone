/* ============================================================
   LitStone — Class Crests & Hero Visual Asset Helpers
   High-fidelity vector icons and illustrations for classes,
   hero powers, totems, and boss encounters.
   ============================================================ */

"use strict";

const ClassCrests = (() => {
  const HERO_CRESTS = {
    Mage: `<svg class="crest-svg crest-mage" viewBox="0 0 64 64" width="100%" height="100%" aria-label="Mage Crest">
      <defs>
        <radialGradient id="mageSphere" cx="45%" cy="40%" r="60%">
          <stop offset="0%" stop-color="#93c5fd"/>
          <stop offset="40%" stop-color="#3b82f6"/>
          <stop offset="75%" stop-color="#1d4ed8"/>
          <stop offset="100%" stop-color="#0f172a"/>
        </radialGradient>
        <linearGradient id="mageRing" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#c084fc"/>
          <stop offset="50%" stop-color="#818cf8"/>
          <stop offset="100%" stop-color="#38bdf8"/>
        </linearGradient>
      </defs>
      <!-- Background magical glow -->
      <circle cx="32" cy="32" r="28" fill="#1e1b4b" stroke="#3b82f6" stroke-width="1.5"/>
      <!-- Astrolabe rings -->
      <ellipse cx="32" cy="32" rx="26" ry="10" transform="rotate(-28 32 32)" fill="none" stroke="url(#mageRing)" stroke-width="1.6" opacity="0.85"/>
      <ellipse cx="32" cy="32" rx="26" ry="10" transform="rotate(42 32 32)" fill="none" stroke="url(#mageRing)" stroke-width="1.6" opacity="0.7"/>
      <!-- Glowing Arcane Orb -->
      <circle cx="32" cy="32" r="14" fill="url(#mageSphere)" stroke="#bfdbfe" stroke-width="1"/>
      <ellipse cx="28" cy="27" rx="5" ry="2.5" transform="rotate(-30 28 27)" fill="#ffffff" opacity="0.6"/>
      <!-- Arcane Runes / Points -->
      <path d="M32 6l2 5-2-1-2 1z M32 58l2-5-2 1-2-1z M6 32l5-2-1 2 1 2z M58 32l-5-2 1 2-1 2z" fill="#93c5fd"/>
      <circle cx="32" cy="32" r="4" fill="#eff6ff"/>
    </svg>`,

    Warrior: `<svg class="crest-svg crest-warrior" viewBox="0 0 64 64" width="100%" height="100%" aria-label="Warrior Crest">
      <defs>
        <linearGradient id="ironSteel" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#cbd5e1"/>
          <stop offset="45%" stop-color="#64748b"/>
          <stop offset="85%" stop-color="#334155"/>
          <stop offset="100%" stop-color="#1e293b"/>
        </linearGradient>
        <linearGradient id="bloodGold" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#fca5a5"/>
          <stop offset="40%" stop-color="#ef4444"/>
          <stop offset="100%" stop-color="#7f1d1d"/>
        </linearGradient>
      </defs>
      <!-- Spiked shield backing -->
      <circle cx="32" cy="32" r="28" fill="#450a0a" stroke="#dc2626" stroke-width="1.5"/>
      <!-- Crossed Battleaxes -->
      <path d="M12 12l40 40 M52 12l-40 40" stroke="#94a3b8" stroke-width="3" stroke-linecap="round"/>
      <!-- Left Axe Head -->
      <path d="M15 15c-4 6-5 13 0 17 4-6 5-13 0-17z" fill="url(#ironSteel)" stroke="#f87171" stroke-width="0.8"/>
      <!-- Right Axe Head -->
      <path d="M49 15c4 6 5 13 0 17-4-6-5-13 0-17z" fill="url(#ironSteel)" stroke="#f87171" stroke-width="0.8"/>
      <!-- Heavy Iron Boss Shield -->
      <path d="M32 16l14 6v14c0 10-14 17-14 17s-14-7-14-17V22z" fill="url(#bloodGold)" stroke="#fecaca" stroke-width="1.5"/>
      <path d="M32 21l9 4v10c0 7-9 12-9 12s-9-5-9-12V25z" fill="url(#ironSteel)"/>
      <circle cx="32" cy="33" r="4" fill="#fca5a5" stroke="#450a0a" stroke-width="1"/>
    </svg>`,

    Priest: `<svg class="crest-svg crest-priest" viewBox="0 0 64 64" width="100%" height="100%" aria-label="Priest Crest">
      <defs>
        <radialGradient id="holyGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stop-color="#fef08a"/>
          <stop offset="55%" stop-color="#eab308"/>
          <stop offset="85%" stop-color="#ca8a04"/>
          <stop offset="100%" stop-color="#422006"/>
        </radialGradient>
      </defs>
      <circle cx="32" cy="32" r="28" fill="#291e0a" stroke="#eab308" stroke-width="1.5"/>
      <!-- Radiant Sunburst Beams -->
      <g stroke="#fde047" stroke-width="1.5" stroke-linecap="round" opacity="0.85">
        <line x1="32" y1="8" x2="32" y2="13"/>
        <line x1="32" y1="51" x2="32" y2="56"/>
        <line x1="8" y1="32" x2="13" y2="32"/>
        <line x1="51" y1="32" x2="56" y2="32"/>
        <line x1="15" y1="15" x2="19" y2="19"/>
        <line x1="45" y1="45" x2="49" y2="49"/>
        <line x1="49" y1="15" x2="45" y2="19"/>
        <line x1="19" y1="45" x2="15" y2="49"/>
      </g>
      <!-- Angelic Wings -->
      <path d="M32 30c-8-12-20-8-22-2 4 4 11 6 17 5 M32 30c8-12 20-8 22-2-4 4-11 6-17 5" fill="none" stroke="#fef08a" stroke-width="2" stroke-linecap="round"/>
      <!-- Holy Chalice / Cross -->
      <path d="M26 25h12c0 8-4 13-6 13s-6-5-6-13z" fill="url(#holyGlow)" stroke="#fef9c3" stroke-width="1"/>
      <path d="M30 38h4v8h-4z M25 46h14v2H25z" fill="url(#holyGlow)"/>
      <circle cx="32" cy="20" r="3.5" fill="#fef08a"/>
    </svg>`,

    Rogue: `<svg class="crest-svg crest-rogue" viewBox="0 0 64 64" width="100%" height="100%" aria-label="Rogue Crest">
      <defs>
        <linearGradient id="venomGlow" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#5eead4"/>
          <stop offset="50%" stop-color="#14b8a6"/>
          <stop offset="100%" stop-color="#042f2e"/>
        </linearGradient>
      </defs>
      <circle cx="32" cy="32" r="28" fill="#042f2c" stroke="#14b8a6" stroke-width="1.5"/>
      <!-- Shadow Assassin Hood Silhouette -->
      <path d="M32 10c-9 4-18 16-18 28 6-2 12 1 18 1s12-3 18-1c0-12-9-24-18-28z" fill="#0f172a" stroke="#0d9488" stroke-width="1"/>
      <!-- Glowing Turquoise Slit Eyes -->
      <ellipse cx="26" cy="26" rx="3" ry="1.2" transform="rotate(-15 26 26)" fill="#5eead4"/>
      <ellipse cx="38" cy="26" rx="3" ry="1.2" transform="rotate(15 38 26)" fill="#5eead4"/>
      <!-- Crossed Poisoned Daggers -->
      <g stroke="#042f2e" stroke-width="0.8">
        <path d="M19 49l13-22 3 3-22 13z" fill="url(#venomGlow)"/>
        <path d="M45 49l-13-22-3 3 22 13z" fill="url(#venomGlow)"/>
        <circle cx="17" cy="51" r="2" fill="#5eead4"/>
        <circle cx="47" cy="51" r="2" fill="#5eead4"/>
      </g>
    </svg>`,

    Paladin: `<svg class="crest-svg crest-paladin" viewBox="0 0 64 64" width="100%" height="100%" aria-label="Paladin Crest">
      <defs>
        <linearGradient id="paladinGold" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#fef08a"/>
          <stop offset="40%" stop-color="#eab308"/>
          <stop offset="85%" stop-color="#854d0e"/>
          <stop offset="100%" stop-color="#451a03"/>
        </linearGradient>
      </defs>
      <circle cx="32" cy="32" r="28" fill="#2d2208" stroke="#eab308" stroke-width="1.5"/>
      <!-- Crusader Kite Shield -->
      <path d="M32 12l16 6v16c0 12-16 20-16 20s-16-8-16-20V18z" fill="url(#paladinGold)" stroke="#fef08a" stroke-width="1.4"/>
      <!-- Radiant Cross on Shield -->
      <path d="M29 20h6v30h-6z" fill="#fef9c3"/>
      <path d="M22 28h20v6H22z" fill="#fef9c3"/>
      <!-- Sacred Diamond Inset -->
      <polygon points="32,27 36,31 32,35 28,31" fill="#38bdf8"/>
    </svg>`,

    Shaman: `<svg class="crest-svg crest-shaman" viewBox="0 0 64 64" width="100%" height="100%" aria-label="Shaman Crest">
      <defs>
        <linearGradient id="stormBlue" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#67e8f9"/>
          <stop offset="50%" stop-color="#0284c7"/>
          <stop offset="100%" stop-color="#082f49"/>
        </linearGradient>
      </defs>
      <circle cx="32" cy="32" r="28" fill="#082830" stroke="#38bdf8" stroke-width="1.5"/>
      <!-- Lightning Bolts Background -->
      <path d="M18 10l8 16h-6l10 18-3-12h7z" fill="#fef08a" opacity="0.85"/>
      <path d="M46 10l-8 16h6l-10 18 3-12h-7z" fill="#fef08a" opacity="0.85"/>
      <!-- Carved Storm Totem Face -->
      <rect x="23" y="16" width="18" height="34" rx="3" fill="url(#stormBlue)" stroke="#7dd3fc" stroke-width="1.2"/>
      <!-- Totem Horns -->
      <path d="M23 20l-6-6v8z M41 20l6-6v8z" fill="#38bdf8"/>
      <!-- Totem Eyes & Teeth -->
      <circle cx="28" cy="27" r="2.2" fill="#ecfeff"/>
      <circle cx="36" cy="27" r="2.2" fill="#ecfeff"/>
      <line x1="26" y1="36" x2="38" y2="36" stroke="#082f49" stroke-width="2"/>
      <line x1="28" y1="34" x2="28" y2="38" stroke="#082f49" stroke-width="1.5"/>
      <line x1="32" y1="34" x2="32" y2="38" stroke="#082f49" stroke-width="1.5"/>
      <line x1="36" y1="34" x2="36" y2="38" stroke="#082f49" stroke-width="1.5"/>
      <!-- Swirling Whirlwind Base -->
      <path d="M20 52c8 4 16 4 24 0-4-3-20-3-24 0z" fill="#67e8f9" opacity="0.9"/>
    </svg>`,
  };

  const POWER_ICONS = {
    Mage: `<svg class="hp-svg" viewBox="0 0 32 32" width="100%" height="100%">
      <path d="M16 2c3 6 8 8 8 15 0 6-4 11-8 11s-8-5-8-11c0-7 5-9 8-15z" fill="#f97316"/>
      <path d="M16 9c2 4 5 5 5 10 0 4-3 7-5 7s-5-3-5-7c0-5 3-6 5-10z" fill="#fde047"/>
      <circle cx="16" cy="21" r="2.5" fill="#ffffff"/>
    </svg>`,

    Warrior: `<svg class="hp-svg" viewBox="0 0 32 32" width="100%" height="100%">
      <path d="M16 4l10 4v9c0 7-10 11-10 11s-10-4-10-11V8z" fill="#64748b" stroke="#f1f5f9" stroke-width="1.2"/>
      <path d="M16 8l6 2v6c0 4-6 7-6 7s-6-3-6-7v-6z" fill="#ef4444"/>
      <circle cx="16" cy="16" r="2" fill="#fef08a"/>
    </svg>`,

    Priest: `<svg class="hp-svg" viewBox="0 0 32 32" width="100%" height="100%">
      <circle cx="16" cy="16" r="13" fill="#ca8a04" stroke="#fef08a" stroke-width="1"/>
      <path d="M13 8h6v16h-6z" fill="#ffffff"/>
      <path d="M8 13h16v6H8z" fill="#ffffff"/>
      <circle cx="16" cy="16" r="2" fill="#fef08a"/>
    </svg>`,

    Rogue: `<svg class="hp-svg" viewBox="0 0 32 32" width="100%" height="100%">
      <path d="M8 24l12-16 4 4-16 12z" fill="#14b8a6" stroke="#042f2e" stroke-width="1"/>
      <path d="M20 8l4-4 2 2-4 4z" fill="#fde047"/>
      <circle cx="25" cy="5" r="1.5" fill="#fef08a"/>
      <line x1="12" y1="18" x2="16" y2="14" stroke="#5eead4" stroke-width="1.5"/>
    </svg>`,

    Paladin: `<svg class="hp-svg" viewBox="0 0 32 32" width="100%" height="100%">
      <path d="M16 4l3 7 7 1-5 5 1 7-6-3-6 3 1-7-5-5 7-1z" fill="#eab308" stroke="#fef08a" stroke-width="1"/>
      <circle cx="16" cy="16" r="3" fill="#ffffff"/>
    </svg>`,

    Shaman: `<svg class="hp-svg" viewBox="0 0 32 32" width="100%" height="100%">
      <rect x="10" y="6" width="12" height="20" rx="2" fill="#0284c7" stroke="#7dd3fc" stroke-width="1"/>
      <circle cx="13" cy="11" r="1.5" fill="#fef08a"/>
      <circle cx="19" cy="11" r="1.5" fill="#fef08a"/>
      <line x1="12" y1="17" x2="20" y2="17" stroke="#082f49" stroke-width="1.5"/>
      <path d="M8 26h16v2H8z" fill="#38bdf8"/>
    </svg>`,
  };

  const TOTEM_ICONS = {
    // Searing Totem (ST)
    ST: `<svg class="totem-svg totem-fire" viewBox="0 0 64 64" width="100%" height="100%" aria-label="Searing Totem">
      <rect x="22" y="16" width="20" height="36" rx="3" fill="#7f1d1d" stroke="#f97316" stroke-width="1.5"/>
      <path d="M32 4c4 6 10 9 10 16 0 7-5 12-10 12s-10-5-10-12c0-7 6-10 10-16z" fill="#ea580c"/>
      <path d="M32 10c2 4 5 6 5 10 0 4-3 7-5 7s-5-3-5-7c0-4 3-6 5-10z" fill="#fde047"/>
      <circle cx="28" cy="30" r="2" fill="#fef08a"/>
      <circle cx="36" cy="30" r="2" fill="#fef08a"/>
    </svg>`,

    // Healing Totem (HE)
    HE: `<svg class="totem-svg totem-water" viewBox="0 0 64 64" width="100%" height="100%" aria-label="Healing Totem">
      <rect x="22" y="16" width="20" height="36" rx="3" fill="#065f46" stroke="#10b981" stroke-width="1.5"/>
      <path d="M32 6c0 0-10 12-10 18 0 6 4 10 10 10s10-4 10-10c0-6-10-18-10-18z" fill="#34d399"/>
      <circle cx="28" cy="28" r="2" fill="#ecfdf5"/>
      <circle cx="36" cy="28" r="2" fill="#ecfdf5"/>
      <path d="M29 36h6v8h-6z M26 39h12v2H26z" fill="#ffffff"/>
    </svg>`,

    // Stonefang Totem (SF)
    SF: `<svg class="totem-svg totem-earth" viewBox="0 0 64 64" width="100%" height="100%" aria-label="Stonefang Totem">
      <rect x="20" y="18" width="24" height="34" rx="2" fill="#475569" stroke="#94a3b8" stroke-width="2"/>
      <path d="M20 18l12-10 12 10z" fill="#334155" stroke="#cbd5e1" stroke-width="1.5"/>
      <rect x="24" y="24" width="6" height="4" fill="#f1f5f9"/>
      <rect x="34" y="24" width="6" height="4" fill="#f1f5f9"/>
      <path d="M26 36l3 4 3-4 3 4 3-4" stroke="#e2e8f0" stroke-width="2" fill="none"/>
    </svg>`,

    // Wrath of Air Totem (WA)
    WA: `<svg class="totem-svg totem-air" viewBox="0 0 64 64" width="100%" height="100%" aria-label="Wrath of Air Totem">
      <rect x="22" y="16" width="20" height="36" rx="3" fill="#0369a1" stroke="#38bdf8" stroke-width="1.5"/>
      <ellipse cx="32" cy="14" rx="14" ry="5" fill="#bae6fd" opacity="0.8"/>
      <ellipse cx="32" cy="8" rx="8" ry="3" fill="#e0f2fe" opacity="0.9"/>
      <circle cx="28" cy="27" r="2.5" fill="#67e8f9"/>
      <circle cx="36" cy="27" r="2.5" fill="#67e8f9"/>
      <path d="M27 38c3 2 7 2 10 0" stroke="#bae6fd" stroke-width="2" fill="none"/>
    </svg>`,
  };

  const BOSS_PORTRAITS = {
    frankenstein: "/static/assets/bosses/frankenstein.jpg",
    van_helsing:  "/static/assets/bosses/van_helsing.jpg",
    moriarty:     "/static/assets/bosses/moriarty.jpg",
  };

  function getCrest(heroClass) {
    return HERO_CRESTS[heroClass] || null;
  }

  function getPowerIcon(heroClass) {
    return POWER_ICONS[heroClass] || null;
  }

  function getTotemIcon(totemCode) {
    return TOTEM_ICONS[totemCode] || null;
  }

  function getBossPortrait(bossId) {
    return BOSS_PORTRAITS[bossId] || null;
  }

  return {
    HERO_CRESTS,
    POWER_ICONS,
    TOTEM_ICONS,
    BOSS_PORTRAITS,
    getCrest,
    getPowerIcon,
    getTotemIcon,
    getBossPortrait,
  };
})();

if (typeof module !== "undefined" && module.exports) {
  module.exports = ClassCrests;
}
