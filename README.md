# Claude Code Skills

Custom skills and subagents for Claude Code. Open this folder in Claude Code (or copy
`.claude/` into another project, or into `~/.claude/` to use them everywhere).

| Skill | What it does | Path |
|---|---|---|
| **google-maps-scraper** | Business leads from Google Maps (browser scraper or official Places API) → CSV/JSON | `.claude/skills/google-maps-scraper` |
| **agency-agents** | A virtual marketing agency: 8 specialist subagents plus an orchestration playbook | `.claude/skills/agency-agents`, `.claude/agents/agency-*.md` |
| **social-media-suite** | LinkedIn, Instagram, Facebook and Xiaohongshu (XHS) posts, calendars and repurposing | `.claude/skills/social-media-suite` |
| **open-seo** | Free SEO audits (script), keyword research, content briefs, schema, local SEO | `.claude/skills/open-seo` |

## Setup

```bash
# Google Maps browser scraper only
pip install playwright && python3 -m playwright install chromium
# optional, official API route
export GOOGLE_MAPS_API_KEY=...
```

The SEO audit script uses only the Python standard library.

## Example prompts

- "Scrape 50 dentists in Kuala Lumpur from Google Maps into a CSV"
- "Act as my agency and build a launch plan for our new skincare line"
- "Turn this blog post into a LinkedIn post, an IG carousel, a FB post and a 小红书 note"
- "Run an SEO audit on https://mysite.com and give me quick wins"
