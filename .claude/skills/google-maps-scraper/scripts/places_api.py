#!/usr/bin/env python3
"""Search Google Places API (New) Text Search and export results.

Usage:
    export GOOGLE_MAPS_API_KEY=...
    python3 places_api.py "dentists in Kuala Lumpur" -o out.csv

Stdlib only. Returns up to 60 results (3 pages of 20).
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import urllib.request

ENDPOINT = "https://places.googleapis.com/v1/places:searchText"
FIELD_MASK = ",".join([
    "places.displayName", "places.rating", "places.userRatingCount", "places.primaryTypeDisplayName",
    "places.formattedAddress", "places.internationalPhoneNumber", "places.websiteUri",
    "places.googleMapsUri", "places.location", "places.businessStatus", "nextPageToken",
])
FIELDS = ["name", "rating", "reviews", "category", "address", "phone", "website",
          "maps_url", "lat", "lng", "status"]


def search(query: str, key: str, max_results: int) -> list[dict]:
    rows, token = [], None
    while len(rows) < max_results:
        body = {"textQuery": query, "pageSize": 20}
        if token:
            body["pageToken"] = token
        req = urllib.request.Request(
            ENDPOINT, data=json.dumps(body).encode(), method="POST",
            headers={"Content-Type": "application/json", "X-Goog-Api-Key": key,
                     "X-Goog-FieldMask": FIELD_MASK})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
        for p in data.get("places", []):
            loc = p.get("location", {})
            rows.append({
                "name": p.get("displayName", {}).get("text", ""),
                "rating": p.get("rating", ""),
                "reviews": p.get("userRatingCount", ""),
                "category": p.get("primaryTypeDisplayName", {}).get("text", ""),
                "address": p.get("formattedAddress", ""),
                "phone": p.get("internationalPhoneNumber", ""),
                "website": p.get("websiteUri", ""),
                "maps_url": p.get("googleMapsUri", ""),
                "lat": loc.get("latitude", ""),
                "lng": loc.get("longitude", ""),
                "status": p.get("businessStatus", ""),
            })
        token = data.get("nextPageToken")
        if not token:
            break
        time.sleep(2)
    return rows[:max_results]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--max", type=int, default=60)
    ap.add_argument("-o", "--output", default="places_results.csv")
    args = ap.parse_args()
    key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not key:
        sys.exit("Set GOOGLE_MAPS_API_KEY (Places API (New) enabled).")
    rows = search(args.query, key, args.max)
    if args.output.endswith(".json"):
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
    else:
        with open(args.output, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(rows)
    print(f"Saved {len(rows)} rows -> {args.output}")


if __name__ == "__main__":
    main()
