# OSINT Multi-Source Pipeline

A small two-stage pipeline for searching many public platforms with one query
and, optionally, pulling full content for whichever results you care about.

**Stage 1 — search (cheap, broad):** `run.py` fans a query out across every
configured adapter in `adapters.py` and writes one JSON file with each
source's hits, normalized to a common schema.

**Stage 2 — enrich (expensive, targeted):** `enrich.py` takes specific
results you've already picked out of that JSON and fetches their full
content (full comment threads, full article text, README, transcript, etc.)
instead of just the short snippet returned by search.

Keeping these separate means you never pay the cost of full-content fetches
for results you're going to ignore.

## Files

| File | Role |
|---|---|
| `core.py` | Shared data model (`UnifiedResult`) and the `SourceAdapter` interface every platform implements |
| `adapters.py` | One adapter class per platform — stage 1, search only |
| `enrich.py` | Stage 2 — fetches full content for a selected result or batch of results |
| `run.py` | CLI entry point that runs stage 1 across chosen sources and writes `results.json` |

## The `UnifiedResult` model

Every adapter returns a list of `UnifiedResult` objects (see `core.py`) so
downstream code — the runner, `enrich.py`, or an LLM consuming the JSON —
never needs to know the per-platform schema:

`source, result_id, title, url, author, created_at, score, text, full_text,
enriched, extra, fetch_error`

- `text` is the short snippet/body available at search time.
- `full_text` / `enriched` are populated only after `enrich.py` runs on that result.
- `extra` holds anything platform-specific worth keeping (subreddit, tags, fork count, etc.) that doesn't fit the common fields.
- `fetch_error` is set instead of raising, so one bad source/result doesn't take down a batch.

## Sources supported

| Source | Auth needed | Notes |
|---|---|---|
| Hacker News | None | Via the Algolia-backed search API |
| Wikipedia | None | |
| Stack Exchange | None (optional key raises quota) | Defaults to Stack Overflow |
| GitHub | None (optional `GITHUB_TOKEN` raises rate limit) | Searches repositories |
| Mastodon | None | Single-instance search (defaults to `mastodon.social`); federation means this isn't all of Mastodon |
| Reddit | None (optional `REDDIT_CLIENT_ID`/`REDDIT_CLIENT_SECRET` for PRAW fallback) | Uses the public `.json` endpoint first |
| YouTube | **Required** — `YOUTUBE_API_KEY` | Google Cloud Data API v3 |
| Lemmy | None | Single-instance search (defaults to `lemmy.world`), same federation caveat as Mastodon |
| Tumblr | **Required** — `TUMBLR_API_KEY` | Tag-based search only (no free-text search API) |
| VK | **Required** — `VK_ACCESS_TOKEN` | Adds Russian/Eastern European coverage |
| Bluesky | Optional — `BLUESKY_HANDLE`/`BLUESKY_APP_PASSWORD` | Implemented in `adapters.py` but commented out of `ALL_ADAPTERS`; public endpoint has known intermittent 403s, app password enables an authed fallback |

Adapters without required credentials return `is_configured() == False` and
`run.py` skips them with a `[skip]` message rather than failing the whole run.

## Installation

```bash
pip install requests python-dotenv praw google-api-python-client youtube-transcript-api
```

Put any API keys/tokens you have into a `.env` file (checked in the script's
own folder, then the parent folder as a fallback):

```
YOUTUBE_API_KEY=...
GITHUB_TOKEN=...
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...
REDDIT_USER_AGENT=osint-pipeline/0.1
TUMBLR_API_KEY=...
VK_ACCESS_TOKEN=...
BLUESKY_HANDLE=...
BLUESKY_APP_PASSWORD=...
STACKEXCHANGE_API_KEY=...
```

All are optional except where marked "Required" above — the pipeline runs
fine with zero keys, just with fewer sources active.

## Usage

### `run.py` — stage 1, search

Writes a JSON file keyed by source name, each value a list of
`UnifiedResult`-shaped dicts, and prints per-source status (`[ok]`, `[skip]`,
`[error]`, `[fail]`) to stderr.

| Case | Command |
|---|---|
| Search all configured sources, default limit (10/source) | `python run.py "your search query"` |
| Limit to specific sources | `python run.py "your search query" --sources reddit,github,hackernews` |
| Change result count per source | `python run.py "your search query" --limit 5` |
| Sources + limit together | `python run.py "your search query" --sources reddit,github --limit 5` |
| Custom output path | `python run.py "your search query" --out my_results.json` |
| All flags together | `python run.py "your search query" --sources reddit,wikipedia --limit 20 --out my_results.json` |
| Unknown source name | Exits with an error listing available sources, nothing is written |

### `enrich.py` — stage 2, full content for selected results

Enrichment is per-source (see `_FETCHERS` in `enrich.py`): full comment
trees for Reddit/Lemmy, full article extract for Wikipedia, README content
for GitHub, transcript for YouTube, reply thread for Bluesky, generic
HTML-stripped page text as the fallback for anything else. All batch-style
modes (`--batch`, `--source`, `--all`) run concurrently via `enrich_batch()`
and capture failures per-item (`fetch_error`) rather than aborting the run.

| Case | Command |
|---|---|
| Single result, explicit source + index | `python enrich.py results.json github 0` |
| Single result, default source (first key in file), index 0 | `python enrich.py results.json` |
| Batch — hand-picked results across any mix of sources | `python enrich.py results.json --batch github:0 reddit:1 youtube:0` |
| Batch — a single source, one result | `python enrich.py results.json --batch reddit:2` |
| Every result from one source | `python enrich.py results.json --source github` |
| Every result from one source, source not present in file | `python enrich.py results.json --source nonexistent` → prints "Enriching 0 items", no error |
| Every result from every source in the file | `python enrich.py results.json --all` |
| Custom results file path (any mode) | `python enrich.py my_results.json --all` |

**Programmatic use** (skip the CLI, call the functions directly — useful
inside a larger script or notebook):

```python
from enrich import fetch_full_text, enrich_batch
from core import UnifiedResult
import json

data = json.loads(open("results.json").read())

# Single result
r = UnifiedResult(**data["github"][0])
full_text = fetch_full_text(r, char_limit=3000)

# All results from one source
selected = [UnifiedResult(**item) for item in data["reddit"]]
enriched = enrich_batch(selected, char_limit=3000, max_workers=5)

# Every result from every source
all_selected = [UnifiedResult(**item) for items in data.values() for item in items]
enriched = enrich_batch(all_selected, char_limit=3000, max_workers=5)
```

## Extending with a new source

1. Add a class in `adapters.py` implementing `SourceAdapter.search()`,
   returning a list of `UnifiedResult`. Override `is_configured()` if it
   needs credentials.
2. Register it in the `ALL_ADAPTERS` dict at the bottom of `adapters.py`.
3. (Optional) Add a matching fetcher function to `_FETCHERS` in `enrich.py`
   if the source has richer full-content available beyond the search snippet.
