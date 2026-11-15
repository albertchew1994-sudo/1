#!/usr/bin/env python3
"""Lightweight on-page / technical SEO audit (Python stdlib only).

Usage:
    python3 seo_audit.py https://example.com
    python3 seo_audit.py https://example.com --crawl 20 --json report.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from html.parser import HTMLParser

UA = "Mozilla/5.0 (compatible; OpenSEO-Audit/1.0)"


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.meta: dict[str, str] = {}
        self.links: list[str] = []
        self.canonical = ""
        self.lang = ""
        self.headings: list[tuple[str, str]] = []
        self.images_no_alt: list[str] = []
        self.images = 0
        self.jsonld: list[str] = []
        self.text_parts: list[str] = []
        self._stack: list[str] = []
        self._buf = ""

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "html":
            self.lang = a.get("lang", "")
        elif tag == "meta":
            key = (a.get("name") or a.get("property") or a.get("http-equiv") or "").lower()
            if key:
                self.meta[key] = a.get("content", "")
        elif tag == "link" and "canonical" in a.get("rel", "").lower():
            self.canonical = a.get("href", "")
        elif tag == "a" and a.get("href"):
            self.links.append(a["href"])
        elif tag == "img":
            self.images += 1
            if not a.get("alt", "").strip():
                self.images_no_alt.append(a.get("src", "")[:120])
        if tag in ("title", "h1", "h2", "h3", "h4", "h5", "h6", "script", "style", "noscript"):
            self._stack.append(tag if tag != "script" or a.get("type") != "application/ld+json" else "jsonld")
            self._buf = ""

    def handle_endtag(self, tag):
        if not self._stack:
            return
        top = self._stack[-1]
        if top == tag or (top == "jsonld" and tag == "script"):
            self._stack.pop()
            text = " ".join(self._buf.split())
            if top == "title":
                self.title = text
            elif top.startswith("h") and len(top) == 2:
                self.headings.append((top, text))
            elif top == "jsonld":
                self.jsonld.append(self._buf)
            self._buf = ""

    def handle_data(self, data):
        if self._stack:
            self._buf += data
            if self._stack[-1] in ("script", "style", "noscript", "jsonld"):
                return
        self.text_parts.append(data)


def fetch(url: str, timeout: int = 20):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read(5_000_000)
            charset = r.headers.get_content_charset() or "utf-8"
            return {"status": r.status, "final_url": r.geturl(), "headers": dict(r.headers),
                    "html": body.decode(charset, "replace"), "bytes": len(body),
                    "ms": int((time.time() - t0) * 1000)}
    except urllib.error.HTTPError as e:
        return {"status": e.code, "final_url": url, "headers": dict(e.headers or {}), "html": "",
                "bytes": 0, "ms": int((time.time() - t0) * 1000)}
    except Exception as e:  # network errors
        return {"status": 0, "final_url": url, "headers": {}, "html": "", "bytes": 0, "ms": 0, "error": str(e)}


def schema_types(blocks: list[str]) -> list[str]:
    out = []
    for b in blocks:
        try:
            data = json.loads(b)
        except json.JSONDecodeError:
            out.append("INVALID_JSON")
            continue
        stack = data if isinstance(data, list) else [data]
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                t = node.get("@type")
                if t:
                    out.extend(t if isinstance(t, list) else [t])
                stack.extend(v for v in node.values() if isinstance(v, (dict, list)))
            elif isinstance(node, list):
                stack.extend(node)
    return sorted(set(map(str, out)))


def audit_page(url: str) -> dict:
    r = fetch(url)
    issues: list[tuple[str, str]] = []
    res = {"url": url, "final_url": r["final_url"], "status": r["status"], "ms": r["ms"],
           "kb": round(r["bytes"] / 1024, 1), "issues": issues}
    if r.get("error"):
        issues.append(("CRITICAL", f"Fetch failed: {r['error']}"))
        return res
    if r["status"] >= 400:
        issues.append(("CRITICAL", f"HTTP {r['status']}"))
        return res
    if r["final_url"].rstrip("/") != url.rstrip("/"):
        issues.append(("INFO", f"Redirected to {r['final_url']}"))
    if not r["final_url"].startswith("https://"):
        issues.append(("CRITICAL", "Page not served over HTTPS"))
    if r["ms"] > 1500:
        issues.append(("WARNING", f"Slow server response: {r['ms']} ms"))
    if r["bytes"] > 2_000_000:
        issues.append(("WARNING", f"Large HTML document: {res['kb']} KB"))

    p = PageParser()
    p.feed(r["html"])
    words = len(" ".join(p.text_parts).split())
    h1s = [t for h, t in p.headings if h == "h1"]
    desc = p.meta.get("description", "")
    robots = (p.meta.get("robots", "") + " " + r["headers"].get("X-Robots-Tag", "")).lower()
    host = urllib.parse.urlparse(r["final_url"]).netloc
    internal, external = set(), set()
    for href in p.links:
        full = urllib.parse.urljoin(r["final_url"], href.split("#")[0])
        if not full.startswith("http"):
            continue
        (internal if urllib.parse.urlparse(full).netloc == host else external).add(full)

    res.update({
        "title": p.title, "title_len": len(p.title), "description": desc, "description_len": len(desc),
        "h1": h1s, "headings": p.headings[:40], "canonical": p.canonical, "lang": p.lang,
        "robots": robots.strip(), "word_count": words, "images": p.images,
        "images_missing_alt": len(p.images_no_alt), "internal_links": sorted(internal),
        "external_links": len(external), "schema": schema_types(p.jsonld),
        "og": {k: v for k, v in p.meta.items() if k.startswith(("og:", "twitter:"))},
    })

    if not p.title:
        issues.append(("CRITICAL", "Missing <title>"))
    elif not 30 <= len(p.title) <= 60:
        issues.append(("WARNING", f"Title length {len(p.title)} (aim 30-60)"))
    if not desc:
        issues.append(("WARNING", "Missing meta description"))
    elif not 70 <= len(desc) <= 160:
        issues.append(("WARNING", f"Meta description length {len(desc)} (aim 70-160)"))
    if len(h1s) == 0:
        issues.append(("CRITICAL", "No H1"))
    elif len(h1s) > 1:
        issues.append(("WARNING", f"{len(h1s)} H1 tags (use one)"))
    levels = [int(h[1]) for h, _ in p.headings]
    if any(b - a > 1 for a, b in zip(levels, levels[1:])):
        issues.append(("INFO", "Heading levels skip (e.g. H2 → H4)"))
    if not p.canonical:
        issues.append(("WARNING", "No canonical tag"))
    elif urllib.parse.urljoin(r["final_url"], p.canonical).rstrip("/") != r["final_url"].rstrip("/"):
        issues.append(("INFO", f"Canonical points elsewhere: {p.canonical}"))
    if "noindex" in robots:
        issues.append(("CRITICAL", "Page is noindex"))
    if not p.lang:
        issues.append(("WARNING", "Missing <html lang>"))
    if "viewport" not in p.meta:
        issues.append(("CRITICAL", "Missing viewport meta (mobile)"))
    if "og:title" not in p.meta or "og:image" not in p.meta:
        issues.append(("WARNING", "Incomplete Open Graph tags (og:title / og:image)"))
    if not p.jsonld:
        issues.append(("INFO", "No JSON-LD structured data"))
    elif "INVALID_JSON" in res["schema"]:
        issues.append(("WARNING", "Invalid JSON-LD block"))
    if p.images_no_alt:
        issues.append(("WARNING", f"{len(p.images_no_alt)}/{p.images} images missing alt text"))
    if words < 300:
        issues.append(("INFO", f"Thin content: {words} words"))
    if len(internal) < 3:
        issues.append(("INFO", f"Few internal links ({len(internal)})"))
    return res


def site_checks(url: str) -> list[tuple[str, str]]:
    base = "{0.scheme}://{0.netloc}".format(urllib.parse.urlparse(url))
    issues = []
    rb = fetch(base + "/robots.txt")
    sitemaps = []
    if rb["status"] == 0:
        return [("CRITICAL", f"Site unreachable: {rb.get('error', 'network error')}")]
    if rb["status"] != 200:
        issues.append(("WARNING", "robots.txt not found"))
    else:
        lines = [line.strip() for line in rb["html"].splitlines()]
        sitemaps = [line.split(":", 1)[1].strip() for line in lines if line.lower().startswith("sitemap:")]
        if any(line.lower().replace(" ", "") == "disallow:/" for line in lines):
            issues.append(("CRITICAL", "robots.txt contains 'Disallow: /'"))
        if not sitemaps:
            issues.append(("INFO", "robots.txt does not reference a sitemap"))
    sm = fetch(sitemaps[0] if sitemaps else base + "/sitemap.xml")
    if sm["status"] != 200:
        issues.append(("WARNING", "No sitemap.xml found"))
    return issues


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--crawl", type=int, default=1, help="max internal pages to audit")
    ap.add_argument("--json", help="write full report to this file")
    args = ap.parse_args()
    url = args.url if args.url.startswith("http") else "https://" + args.url

    queue, seen, pages = [url], set(), []
    while queue and len(pages) < args.crawl:
        u = queue.pop(0)
        if u in seen:
            continue
        seen.add(u)
        page = audit_page(u)
        pages.append(page)
        print(f"Audited {u} [{page['status']}]", file=sys.stderr)
        for link in page.get("internal_links", []):
            if link not in seen and not link.lower().endswith((".pdf", ".jpg", ".png", ".zip")):
                queue.append(link)

    site = site_checks(url)
    dupes = defaultdict(list)
    for pg in pages:
        for key in ("title", "description"):
            if pg.get(key):
                dupes[(key, pg[key])].append(pg["url"])
    dup_issues = [("WARNING", f"Duplicate {k} on {len(v)} pages: '{t[:60]}'")
                  for (k, t), v in dupes.items() if len(v) > 1]

    print(f"\n=== SEO AUDIT: {url} ===")
    for sev, msg in site + dup_issues:
        print(f"  [{sev}] (site) {msg}")
    for pg in pages:
        print(f"\n--- {pg['url']}  status={pg['status']}  {pg['ms']}ms  {pg['kb']}KB")
        if "title" in pg:
            print(f"  Title ({pg['title_len']}): {pg['title']}")
            print(f"  Description ({pg['description_len']}): {pg['description'][:160]}")
            print(f"  H1: {pg['h1']}  | words: {pg['word_count']}  | schema: {pg['schema'] or '-'}")
            print(f"  Links: {len(pg['internal_links'])} internal / {pg['external_links']} external"
                  f"  | images missing alt: {pg['images_missing_alt']}/{pg['images']}")
        order = {"CRITICAL": 0, "WARNING": 1, "INFO": 2}
        for sev, msg in sorted(pg["issues"], key=lambda i: order[i[0]]):
            print(f"  [{sev}] {msg}")

    all_issues = site + dup_issues + [i for pg in pages for i in pg["issues"]]
    counts = {s: sum(1 for i in all_issues if i[0] == s) for s in ("CRITICAL", "WARNING", "INFO")}
    score = max(0, 100 - 15 * counts["CRITICAL"] // len(pages) - 4 * counts["WARNING"] // len(pages))
    print(f"\nSummary: {counts}  | heuristic score: {score}/100")

    if args.json:
        for pg in pages:
            pg["internal_links"] = pg.get("internal_links", [])[:50]
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({"url": url, "score": score, "counts": counts, "site_issues": site + dup_issues,
                       "pages": pages}, f, ensure_ascii=False, indent=2)
        print(f"Full report -> {args.json}")


if __name__ == "__main__":
    main()
