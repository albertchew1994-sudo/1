---
name: open-seo
description: Open-source, free-tool SEO workflow — technical and on-page audits of any URL (titles, meta, headings, canonical, robots.txt, sitemap, schema, images, links, Open Graph, speed basics), keyword research, content briefs, content optimisation, local SEO and schema generation. Use when the user asks to audit a website, improve rankings, research keywords, write an SEO brief/article, or generate schema markup.
---

# Open SEO

No paid tools required. Uses `scripts/seo_audit.py` (Python stdlib only) plus web search.

## 1. Technical and on-page audit

```bash
python3 .claude/skills/open-seo/scripts/seo_audit.py https://example.com            # single page
python3 .claude/skills/open-seo/scripts/seo_audit.py https://example.com --crawl 20 # crawl up to 20 internal pages
python3 .claude/skills/open-seo/scripts/seo_audit.py https://example.com --json report.json
```

The script checks: HTTP status and redirects, response time, HTML size, `<title>` (length),
meta description (length), H1 count and heading outline, canonical, meta robots / X-Robots-Tag,
`lang`, viewport, Open Graph and Twitter tags, JSON-LD schema types, images without `alt`,
internal and external link counts, word count, robots.txt and sitemap.xml presence, and
duplicate titles/descriptions across crawled pages. Each issue is tagged
`CRITICAL / WARNING / INFO`.

Then add judgement the script can't: Is the title compelling? Does the content match search
intent? Is the internal linking logical? For Core Web Vitals, point the user to PageSpeed
Insights (`https://pagespeed.web.dev/?url=<url>`) or run Lighthouse if it's available.

**Report format:** Score summary → Critical fixes → Warnings → Opportunities, split into quick
wins (under 1 day) and strategic work. Every item gets: issue · why it matters · exact fix
(with code where relevant).

## 2. Keyword research (free method)

1. Seed list from the user's products, services and customer language.
2. Expand with web search: "People also ask", related searches, autocomplete modifiers
   (best, vs, how to, near me, price, for beginners, the year), Reddit/Quora questions, and
   competitor page titles.
3. Classify each keyword by **intent** (informational / commercial / transactional /
   navigational) and **funnel stage**.
4. Estimate difficulty qualitatively from the SERP: are the top 10 big brands or forums/small
   sites? Label it as an estimate. Never invent search volumes. If the user has Google Search
   Console, Keyword Planner, Ahrefs or Semrush data, use that instead.
5. Cluster into topics → one page per cluster → a keyword map table:
   `Cluster | Primary KW | Secondary KWs | Intent | Target URL (existing/new) | Priority`.

## 3. Content brief

Target keyword · intent · audience · recommended title (≤ 60 chars) and meta description
(≤ 155 chars) · URL slug · H2/H3 outline · entities and subtopics to cover (from top-ranking
pages) · FAQs (from People also ask) · internal links to and from · external sources to cite ·
schema type · word count range (based on the SERP, not a fixed number) · CTA.

## 4. Writing and optimising content

- Answer the query in the first 100 words; use the primary keyword naturally in the title, H1,
  first paragraph, one H2 and the slug.
- Show E-E-A-T: first-hand experience, author bio, sources, updated date.
- Use scannable structure: short paragraphs, lists, tables, a TL;DR.
- Never keyword-stuff or create doorway pages.

## 5. Schema (JSON-LD) generator

Generate valid JSON-LD for: Organization, LocalBusiness, Product, Article/BlogPosting, FAQPage,
HowTo, BreadcrumbList, Event, Review. Output a `<script type="application/ld+json">` block and
remind the user to test it at https://search.google.com/test/rich-results.

## 6. Local SEO checklist

Google Business Profile complete (categories, hours, photos, services, posts, Q&A) · consistent
NAP everywhere · LocalBusiness schema · location pages with unique content · a review generation
and response process · local citations and directories · embedded map. Pairs well with the
`google-maps-scraper` skill to benchmark competitors' ratings and review counts.

## 7. Off-page (white-hat only)

Digital PR, linkable assets (data studies, tools, guides), partner and supplier pages, guest
contributions on relevant sites, and unlinked brand mentions. Never recommend buying links or
PBNs.
