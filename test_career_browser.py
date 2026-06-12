"""
test_career_browser.py — Browser E2E for Literary Career (Playwright).

Requires: pip install playwright && playwright install chromium
"""

import json

import pytest

from career_test_support import CHAPTER_NAMES, setup_lethal_turn
from server import GAMES

pytestmark = pytest.mark.browser

_MULLIGAN_BTN_READY = "() => !document.getElementById('btn-mulligan-confirm')?.disabled"
_ACTIVE_GAME_READY = """() => {
  try {
    const raw = localStorage.getItem("litstoneActiveGame");
    return !!(raw && JSON.parse(raw).gameId);
  } catch (_) {
    return false;
  }
}"""


def _clear_browser_storage(page) -> None:
    page.evaluate("""() => {
      localStorage.removeItem("litstoneCampaignProgress");
      localStorage.removeItem("litstoneActiveGame");
    }""")


def _active_game_id(page) -> str:
    raw = page.evaluate("""() => localStorage.getItem("litstoneActiveGame")""")
    if not raw:
        return ""
    return json.loads(raw).get("gameId", "")


def _browser_lethal_win(page) -> str:
    gid = _active_game_id(page)
    assert gid and gid in GAMES, f"Expected active game in GAMES, got {gid!r}"
    setup_lethal_turn(GAMES[gid])
    return page.evaluate("""async () => {
      const meta = JSON.parse(localStorage.getItem("litstoneActiveGame") || "{}");
      const res = await fetch("/api/action", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          game_id: meta.gameId,
          action: "attack",
          idx: 0,
          target: "hero",
        }),
      });
      const data = await res.json();
      if (typeof onGameStateUpdated === "function") {
        onGameStateUpdated(data, null);
      }
      return data.winner || "";
    }""")


def _wait_loading_done(page) -> None:
    page.wait_for_function("""() => {
      const el = document.getElementById("loading-overlay");
      return !el || el.classList.contains("hidden");
    }""")


def _confirm_mulligan(page, *, track_response: bool = False) -> None:
    page.wait_for_selector("#screen-mulligan.active")
    page.wait_for_function(_MULLIGAN_BTN_READY)
    if track_response:
        with page.expect_response(
            lambda r: "/api/mulligan" in r.url and r.request.method == "POST" and r.status == 200
        ):
            page.click("#btn-mulligan-confirm")
    else:
        page.click("#btn-mulligan-confirm")
    page.wait_for_selector("#screen-game.active")


def _wait_for_match_ready(page) -> str:
    page.wait_for_selector("#screen-game.active")
    page.wait_for_function(_ACTIVE_GAME_READY)
    return _active_game_id(page)


def _open_career_map(page, base: str, *, clear_storage: bool = True) -> None:
    page.goto(base)
    page.wait_for_selector("#screen-hub.active")
    if clear_storage:
        _clear_browser_storage(page)
    page.click("button.hub-mode--career")
    page.wait_for_selector("#screen-campaign.active")


def _start_chapter_from_map(page, chapter_name: str) -> None:
    page.wait_for_function(
        """(name) => {
          const btn = [...document.querySelectorAll("button.campaign-node")]
            .find(el => el.querySelector(".campaign-node-name")?.textContent === name);
          return btn && !btn.disabled;
        }""",
        arg=chapter_name,
    )
    page.locator("button.campaign-node").filter(
        has=page.locator(".campaign-node-name", has_text=chapter_name)
    ).click()
    page.wait_for_selector("#screen-menu.active")


def _pick_mage_starter_and_start(page) -> None:
    page.locator('.hero-card[data-class="Mage"]').click()
    page.wait_for_selector("#screen-deck.active")
    page.click("button.btn-starter-deck")
    page.wait_for_function("() => !document.getElementById('btn-start-ai')?.disabled")
    page.click("#btn-start-ai")
    _confirm_mulligan(page)


def _advance_via_winner_next(page) -> None:
    page.wait_for_selector("#btn-winner-next:not(.hidden)")
    with page.expect_response(
        lambda r: "/api/new_game" in r.url and r.request.method == "POST" and r.status == 200
    ):
        page.click("#btn-winner-next")
    _wait_loading_done(page)
    page.wait_for_selector("#screen-mulligan.active, #screen-game.active")
    if page.locator("#screen-mulligan.active").count():
        _confirm_mulligan(page, track_response=True)
    _wait_for_match_ready(page)


@pytest.mark.browser
def test_career_map_lists_six_chapters(browser_page):
    page, base = browser_page
    _open_career_map(page, base)

    assert page.locator("button.campaign-node").count() == len(CHAPTER_NAMES)
    labels = page.locator(".campaign-node-name").all_text_contents()
    for expected in CHAPTER_NAMES:
        assert expected in labels


@pytest.mark.browser
def test_career_first_chapter_reaches_match(browser_page):
    page, base = browser_page
    _open_career_map(page, base)
    _start_chapter_from_map(page, CHAPTER_NAMES[0])
    _pick_mage_starter_and_start(page)

    assert _active_game_id(page)
    page.wait_for_selector("#screen-game.active")


@pytest.mark.browser
def test_full_career_browser_start_to_finish(browser_page):
    page, base = browser_page
    _open_career_map(page, base)

    for i, chapter in enumerate(CHAPTER_NAMES):
        if i == 0:
            _start_chapter_from_map(page, chapter)
            _pick_mage_starter_and_start(page)
            _wait_for_match_ready(page)
        else:
            page.wait_for_selector("#winner-overlay:not(.hidden)")
            _advance_via_winner_next(page)

        winner = _browser_lethal_win(page)
        assert winner == "Player", f"Chapter {chapter} should be a player win"

        page.wait_for_selector("#winner-overlay:not(.hidden)")
        if i == len(CHAPTER_NAMES) - 1:
            page.wait_for_function(
                """() => {
                  const t = document.getElementById("winner-text")?.textContent || "";
                  return t === "Anthology Complete!" || t === "Victory!";
                }"""
            )

    completed = page.evaluate(
        """() => JSON.parse(localStorage.getItem("litstoneCampaignProgress") || "[]")"""
    )
    assert len(completed) == len(CHAPTER_NAMES)
    assert completed[-1] == "n6"
