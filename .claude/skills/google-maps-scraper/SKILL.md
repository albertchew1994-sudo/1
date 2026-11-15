---
name: google-maps-scraper
description: Collect business listings (name, rating, review count, category, address, phone, website, Maps URL) from Google Maps for a search query such as "dentists in Kuala Lumpur" and export them to CSV/JSON. Use when the user wants local business leads, a list of places, competitor locations, or to "scrape Google Maps".
---

# Google Maps Scraper

Turn a Google Maps search ("cafes in Petaling Jaya", "plumbers near Austin TX") into a clean
lead list.

## Choose the method

| Method | When | Notes |
|---|---|---|
| **A. Places API (official)** | User has a Google Cloud API key, needs reliability or commercial use | `scripts/places_api.py`. ToS-compliant, paid per request, max 60 results per query (3 pages). |
| **B. Browser scraper** | Quick research, no API key | `scripts/gmaps_scraper.py`. Uses Playwright to drive Google Maps like a user. Can break when Google changes its markup; respect Google's Terms of Service and local data-protection law (PDPA/GDPR) when storing personal data. |

Default to **A** if `GOOGLE_MAPS_API_KEY` is set, otherwise **B**.

## Method A: Places API

```bash
export GOOGLE_MAPS_API_KEY=...        # Places API (New) must be enabled
python3 .claude/skills/google-maps-scraper/scripts/places_api.py "dentists in Kuala Lumpur" -o dentists.csv
```

## Method B: Browser scraper

One-time setup:

```bash
pip install playwright
python3 -m playwright install chromium
```

Run:

```bash
python3 .claude/skills/google-maps-scraper/scripts/gmaps_scraper.py "dentists in Kuala Lumpur" \
  --max 50 -o dentists.csv          # .json also supported
# options: --headful (watch the browser), --lang en, --no-details (faster, list-page data only)
```

Columns: `name, rating, reviews, category, address, phone, website, plus_code, maps_url, lat, lng`.

## Workflow

1. Clarify the **query** (business type + location) and **how many** results. Split big areas into
   smaller ones ("cafes in Bangsar", "cafes in Mont Kiara"…) since one Maps search tops out around
   120 results.
2. Run the script. For multiple queries, loop and then de-duplicate by `maps_url`.
3. Clean: drop rows without phone/website if the user wants contactable leads; normalise phone
   numbers to E.164 when the country is known.
4. Summarise: count, average rating, % with website, and the top 10 by reviews. Offer to save to
   Google Sheets or enrich (emails, socials) via another tool.

## Troubleshooting

- **0 results / consent page**: run with `--headful` once; in the EU accept the consent dialog. Try `--lang en`.
- **Blocked / captcha**: slow down (`--delay 2`), reduce `--max`, or switch to Method A.
- **Selectors broke**: open the page with `--headful`, inspect, and update the selectors at the top of `gmaps_scraper.py`.
