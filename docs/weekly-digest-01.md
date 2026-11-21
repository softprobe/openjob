# The Agent Job Market — Edition 1 (Fri Nov 20, 2026)

**Status:** DRAFT — not sent, not published. First edition of the weekly digest (X6).
**Cadence:** every Monday (this first edition is dated Fri Nov 20, 2026 because the digest launches with the Day-2 batch; from next week it goes out Mondays, alongside the Monday snapshot in the data-stories skill).
**Format:** one email + one page on the site. Same text in both; no separate versions.

## Honest-numbers note (read before sending)

- **Dataset total: 33,362 rows** (snapshot as of Fri Nov 20, 2026). **Never present this as live jobs.**
- **Fresh jobs: ~14,000 posted in the last 60 days.** This is the Nov 18 estimate (44.0% fresh in the n=5,107 sample; 41.9% ATS-weighted). The fresh share has **not** been recomputed on the new 33,362-row snapshot yet — the next Monday snapshot recomputes it with the same 6 shard indices and definitions. Until then, "~14,000" is carried forward from Nov 18 and labelled as such below.
- **No week-over-week delta exists yet.** Only one dataset snapshot has been computed so far (Nov 18). There is no prior week to compare against, so this edition reports levels only and says so plainly. The first real delta appears in Edition 2, once the second Monday snapshot exists. Do not invent a trend.
- All other percentages below are from the Nov 18 sample (n=5,107, both sha256s verified): top 10 employers 48.2%; AI-agent roles 1.5% narrow / 6.7% broad; salary on 6.2% of rows, all Ashby, median posted range $150K–$205K (Ashby only); China 33.9%, US 27.4%; explicitly remote 9.7%, 68% unspecified. Definitions and caveats: see `skills/openjob-data-stories`.

---

## Edition 1 — the email / page text

**Subject / title: The Agent Job Market — Edition 1: 33,362 rows indexed, ~14,000 fresh**

I maintain OpenJob, a public job database for AI agents (https://openjob.softprobe.ai). Every Monday I count the same index the same way and publish what changed. This is the first edition — so this week is levels only, no trend yet. The first week-over-week delta comes in Edition 2, once a second snapshot exists.

**The index this week**
- 33,362 rows indexed in total (snapshot Fri Nov 20, 2026).
- ~14,000 of them were posted in the last 60 days (Nov 18 estimate; fresh share to be recomputed on the next Monday snapshot). The rest is older archive data — filter by date before you treat a row as a live opening.

**AI-agent roles: 1.5% narrow, 6.7% broad (Nov 18 sample, n=5,107)**
- Narrow set (agent/agents/agentic/LLM/GenAI/generative AI/prompt engineer/copilot in the title): 76 roles, 1.5% of the index.
- Broad AI/ML set: 341 roles, 6.7%.
- Agent work is real but small: it concentrates at a handful of employers rather than spreading across the index.

**Top employers: 10 employers hold 48.2% of the index (Nov 18 sample)**
- Top 5 alone are 32.7%. Leaders in the sample: Cloudflare (493 rows), DJI (425), 远景能源 Envision Energy (312), Stripe (222), 新浪微博 Sina Weibo (220), 阶跃星辰 StepFun (220).
- The index is 81 distinct employers in the sample — concentrated, not long-tail. If your agent only watches the big boards, it is mostly watching ten companies.

**One notable role**
- Scale AI — "Frontier Agents Engineer". One of the named agent roles in the index, and the clearest example of the category: an employer hiring specifically to build frontier agents, not to use them. (Title as listed by the employer; check the live posting on the employer's own board via the `source_url` on openjob.softprobe.ai before applying — postings move and close.)

**What to watch next week**
- Edition 2 adds the first real delta: fresh count, AI-agent share, and top-10 concentration, week over week, same shard indices, same definitions.

**How we count:** "Fresh" = posted date on or after 60 days before the snapshot date; `posted` is the date the employer states on its own board. Percentages are sample percentages (n=5,107, Nov 18) unless marked full-dataset or ATS-weighted. Indexed ≠ recruited — OpenJob did not recruit these employers; the employers own the text. Salary medians describe Ashby-posted roles only (n=257 parseable ranges). Full method: https://github.com/softprobe/openjob

OpenJob is free and open source: https://github.com/softprobe/openjob — your agent can search the index over MCP at https://openjob.softprobe.ai/api/mcp

---

## Pre-send checklist (for the executor)

- [ ] Recompute the fresh share on the Monday snapshot before Edition 2; do not carry "~14,000" forward silently a second week.
- [ ] Verify the Scale AI role is still listed (via its `source_url`) before naming it again.
- [ ] Numbers re-checked against `skills/openjob-data-stories`, not from memory.
- [ ] 33,362 never presented as live jobs.
