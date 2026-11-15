---
name: agency-agents
description: Run a virtual full-service marketing agency — strategist, copywriter, designer, SEO specialist, social media manager, performance marketer, data analyst and project manager — as specialist subagents. Use when the user wants a campaign, launch, client deliverable, or any multi-discipline marketing task handled "like an agency", or asks for a specific agency role.
---

# Agency Agents

A team of specialist subagents defined in `.claude/agents/agency-*.md`.

| Agent | Use for |
|---|---|
| `agency-project-manager` | Scoping a request, planning, delegating, client updates |
| `agency-strategist` | Positioning, personas, messaging, channel plan |
| `agency-copywriter` | Ads, landing pages, emails, hooks, scripts |
| `agency-designer` | Creative concepts, visual direction, image prompts |
| `agency-seo-specialist` | Keywords, audits, content briefs (uses `open-seo`) |
| `agency-social-media-manager` | LinkedIn / Instagram / Facebook / XHS content (uses `social-media-suite`) |
| `agency-performance-marketer` | Paid campaigns, targeting, budgets, A/B tests |
| `agency-data-analyst` | Reports, funnels, attribution, insights |

## How to run a job

1. **Single-discipline ask** (e.g. "write 5 ad hooks") → hand straight to the matching agent.
2. **Multi-discipline ask** (e.g. "launch plan for our new skincare line") → follow the pipeline:
   1. `agency-project-manager` writes the brief and plan.
   2. `agency-strategist` sets audience, positioning and channels.
   3. In parallel: `agency-copywriter`, `agency-designer`, `agency-seo-specialist`,
      `agency-social-media-manager`, `agency-performance-marketer` produce their pieces,
      each given the strategy brief as context.
   4. `agency-data-analyst` defines KPIs and the measurement plan.
   5. The project manager consolidates everything into one client-ready deliverable.
3. Pass each agent the full context it needs (brief, brand voice, prior outputs); subagents
   do not see the main conversation.

## Intake questions (ask only what's missing)

Business/product · goal & KPI · target audience · market/language · budget · timeline ·
brand voice or examples · channels already in use.

## Deliverable format

One consolidated document: Executive summary → Strategy → Creative & copy → Channel plans
(SEO, social, paid) → Measurement → Timeline & owners → Open questions.
