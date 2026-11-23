"""Capture README/report screenshots with the locally installed Chrome.

Usage (with the Flask app running on port 5055)::

    python scripts/capture_screenshots.py

Screenshots are written to ``docs/screenshots/``.
"""

from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "screenshots"
LOCAL = "http://127.0.0.1:5055"
LIVE = "https://mukeshbtech989-png.github.io/cits-skill-gap-analyzer/"

DESKTOP_SHOTS = [
    ("dashboard.png", f"{LOCAL}/"),
    ("student-report.png", f"{LOCAL}/students/3"),
    ("static-demo.png", LIVE),
]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})

        for name, url in DESKTOP_SHOTS:
            page.set_viewport_size({"width": 1440, "height": 900})
            page.goto(url, wait_until="networkidle")
            page.screenshot(path=str(OUT_DIR / name), full_page=True)
            print(f"saved docs/screenshots/{name}")

        page.set_viewport_size({"width": 430, "height": 900})
        page.goto(LIVE, wait_until="networkidle")
        page.screenshot(path=str(OUT_DIR / "static-demo-mobile.png"), full_page=True)
        print("saved docs/screenshots/static-demo-mobile.png")

        browser.close()


if __name__ == "__main__":
    main()
