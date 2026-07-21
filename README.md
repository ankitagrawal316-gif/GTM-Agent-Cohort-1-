# Signal Radar — Explicit Intent + Firmographic Triggers

## Section 1: Explicit Stated Intent

| Platform | Status |
|---|---|
| Hacker News | Live — Algolia public API, no auth |
| Reddit | On hold — see below |
| Upwork | Pending — needs API approval + ToS review before building outreach on top of it |

**Reddit is on hold**: Reddit closed self-service API registration under its
"Responsible Builder Policy." New apps now require manual approval, and the
policy explicitly states commercial use of Reddit data requires express
written approval before any access. No env vars needed for this build since
the endpoint just returns an explanatory 501 — revisit once/if approval comes
through.

## Section 2: Firmographic & Technographic Triggers

| Source | Status |
|---|---|
| GDELT News | Live — free, no key, global news full-text search |
| SEC EDGAR | Live — free, official, no key, US public company filings only |
| Tech stack (BuiltWith/Wappalyzer) | Pending — requires a paid API key, not wired up |

No environment variables required for either — both are genuinely open APIs.

### A note on data quality here

Neither `api.gdeltproject.org` nor `efts.sec.gov` could be tested live from
the environment this was built in (sandboxed, domain-restricted). Both are
built against their documented API contracts, but if response fields don't
match what the code expects once deployed (check Vercel's function logs),
that's the first place to look — the API shape may have shifted, or query
syntax may need adjusting per platform's current docs:
- GDELT: https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/
- SEC EDGAR full-text search: https://www.sec.gov/edgar/search/

### On SEC EDGAR coverage

This only covers **US publicly traded companies** filing 8-Ks — a small
slice of your actual ICP, which is mostly private mid-market companies.
Treat this as a bonus signal for the subset of prospects that happen to be
public, not a primary source. GDELT's global news coverage is the broader
net here.

## Deploy

Same as before: push to GitHub, import into Vercel, leave Root Directory
blank, deploy. No new environment variables needed for this version.
