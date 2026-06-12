"""Shared pytest fixtures for LitStone."""

import socket
import threading
import time
import urllib.error
import urllib.request

import pytest


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture(scope="module")
def live_server():
    """Run the Flask app on a local port (same process — shares GAMES dict)."""
    from server import GAMES, app

    GAMES.clear()
    port = _free_port()
    base = f"http://127.0.0.1:{port}"

    thread = threading.Thread(
        target=lambda: app.run(
            host="127.0.0.1",
            port=port,
            threaded=True,
            use_reloader=False,
        ),
        daemon=True,
    )
    thread.start()

    for _ in range(60):
        try:
            with urllib.request.urlopen(f"{base}/api/health", timeout=0.25) as res:
                if res.status == 200:
                    break
        except (urllib.error.URLError, TimeoutError):
            time.sleep(0.1)
    else:
        pytest.fail("Flask server did not become ready in time")

    yield base
    GAMES.clear()


@pytest.fixture(scope="module")
def browser_page(live_server):
    """Headless Chromium page pointed at the live server."""
    pytest.importorskip("playwright")
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        page.set_default_timeout(15_000)
        yield page, live_server
        context.close()
        browser.close()
