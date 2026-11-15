#!/usr/bin/env python3
"""Scrape Google Maps search results with Playwright.

Usage:
    python3 gmaps_scraper.py "dentists in Kuala Lumpur" --max 50 -o out.csv

Requires: pip install playwright && python3 -m playwright install chromium
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.parse

try:
    from playwright.sync_api import TimeoutError as PWTimeout
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover
    sys.exit("Playwright missing. Run: pip install playwright && python3 -m playwright install chromium")

# --- Selectors (update here if Google changes its markup) ---------------------
FEED = 'div[role="feed"]'
RESULT_LINK = 'a[href*="/maps/place/"]'
END_OF_LIST = "text=/You've reached the end of the list/i"
DETAIL_NAME = "h1"
DETAIL_RATING = 'div.F7nice span[aria-hidden="true"]'
DETAIL_REVIEWS = 'div.F7nice span[aria-label*="review"]'
DETAIL_CATEGORY = 'button[jsaction*="category"]'
DETAIL_ADDRESS = 'button[data-item-id="address"]'
DETAIL_PHONE = 'button[data-item-id^="phone:tel:"]'
DETAIL_WEBSITE = 'a[data-item-id="authority"]'
DETAIL_PLUS = 'button[data-item-id="oloc"]'

FIELDS = ["name", "rating", "reviews", "category", "address", "phone",
          "website", "plus_code", "maps_url", "lat", "lng"]


def _text(page, selector: str) -> str:
    loc = page.locator(selector).first
    try:
        if loc.count() == 0:
            return ""
        label = loc.get_attribute("aria-label") or ""
        txt = loc.inner_text(timeout=1500).strip()
        # address/phone buttons expose a clean value in aria-label ("Address: ...")
        if label and ":" in label and selector.startswith("button[data-item-id"):
            return label.split(":", 1)[1].strip()
        return txt
    except PWTimeout:
        return ""


def _coords(url: str) -> tuple[str, str]:
    m = re.search(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", url) or re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", url)
    return (m.group(1), m.group(2)) if m else ("", "")


def collect_links(page, max_results: int, delay: float) -> list[dict]:
    page.wait_for_selector(f"{FEED}, {DETAIL_NAME}", timeout=20000)
    if page.locator(FEED).count() == 0:  # single-result query lands on a place page
        return [{"maps_url": page.url, "name": _text(page, DETAIL_NAME)}]

    feed = page.locator(FEED)
    seen: dict[str, dict] = {}
    stale = 0
    while len(seen) < max_results and stale < 6:
        before = len(seen)
        for a in page.locator(f"{FEED} {RESULT_LINK}").all():
            href = a.get_attribute("href") or ""
            if href and href not in seen:
                seen[href] = {"maps_url": href, "name": a.get_attribute("aria-label") or ""}
        if page.locator(END_OF_LIST).count():
            break
        feed.evaluate("el => el.scrollBy(0, el.scrollHeight)")
        time.sleep(delay)
        stale = stale + 1 if len(seen) == before else 0
    return list(seen.values())[:max_results]


def scrape_details(page, item: dict, delay: float) -> dict:
    row = {k: "" for k in FIELDS}
    row.update(item)
    try:
        page.goto(item["maps_url"], wait_until="domcontentloaded", timeout=30000)
        page.wait_for_selector(DETAIL_NAME, timeout=15000)
        time.sleep(delay)
    except PWTimeout:
        return row
    row["name"] = _text(page, DETAIL_NAME) or row["name"]
    row["rating"] = _text(page, DETAIL_RATING)
    reviews = page.locator(DETAIL_REVIEWS).first
    if reviews.count():
        row["reviews"] = re.sub(r"[^\d]", "", reviews.get_attribute("aria-label") or "")
    row["category"] = _text(page, DETAIL_CATEGORY)
    row["address"] = _text(page, DETAIL_ADDRESS)
    row["phone"] = _text(page, DETAIL_PHONE)
    site = page.locator(DETAIL_WEBSITE).first
    row["website"] = site.get_attribute("href") if site.count() else ""
    row["plus_code"] = _text(page, DETAIL_PLUS)
    row["lat"], row["lng"] = _coords(page.url)
    return row


def write(rows: list[dict], path: str) -> None:
    if path.endswith(".json"):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
    else:
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("query")
    ap.add_argument("--max", type=int, default=20)
    ap.add_argument("-o", "--output", default="gmaps_results.csv")
    ap.add_argument("--lang", default="en")
    ap.add_argument("--delay", type=float, default=1.2, help="seconds between actions")
    ap.add_argument("--headful", action="store_true")
    ap.add_argument("--no-details", action="store_true", help="only collect names + URLs")
    args = ap.parse_args()

    url = f"https://www.google.com/maps/search/{urllib.parse.quote_plus(args.query)}?hl={args.lang}"
    with sync_playwright() as p:
        launch = {"headless": not args.headful}
        if os.environ.get("CHROMIUM_PATH"):
            launch["executable_path"] = os.environ["CHROMIUM_PATH"]
        browser = p.chromium.launch(**launch)
        ctx = browser.new_context(locale=args.lang, viewport={"width": 1280, "height": 900})
        page = ctx.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
        # Dismiss the cookie consent screen if shown (EU)
        for label in ("Accept all", "Reject all"):
            btn = page.get_by_role("button", name=label)
            if btn.count():
                btn.first.click()
                break

        items = collect_links(page, args.max, args.delay)
        print(f"Found {len(items)} listings", file=sys.stderr)
        rows = []
        for i, item in enumerate(items, 1):
            if args.no_details:
                row = {k: "" for k in FIELDS}
                row.update(item)
                row["lat"], row["lng"] = _coords(item["maps_url"])
            else:
                row = scrape_details(page, item, args.delay)
                print(f"[{i}/{len(items)}] {row['name']}", file=sys.stderr)
            rows.append(row)
        browser.close()

    write(rows, args.output)
    print(f"Saved {len(rows)} rows -> {args.output}")


if __name__ == "__main__":
    main()
