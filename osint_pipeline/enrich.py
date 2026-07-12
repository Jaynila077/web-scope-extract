"""
Stage 2: fetch full content for a *selected* UnifiedResult, on demand.

Kept deliberately separate from adapters.py (stage 1 / search) -- this is
the expensive step, meant to run only on results you've already decided
are worth reading in full, not on every search hit.

Usage:
    from enrich import fetch_full_text
    full = fetch_full_text(result, char_limit=3000)
"""

from __future__ import annotations

import re
import requests

from core import UnifiedResult

DEFAULT_TIMEOUT = 10.0
DEFAULT_CHAR_LIMIT = 3000  # generous but bounded, good for testing full-fetch without runaway payloads


def _strip_html(html: str) -> str:
    text = re.sub(r"<script.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _fetch_generic_page_text(url: str, char_limit: int) -> str:
    """Fallback: fetch any URL and strip HTML tags down to plain text."""
    headers = {"User-Agent": "osint-pipeline/0.1 (research use)"}
    resp = requests.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
    resp.raise_for_status()
    return _strip_html(resp.text)[:char_limit]


def _fetch_reddit_full(result: UnifiedResult, char_limit: int) -> str:
    """Full comment tree via the .json endpoint, flattened to text."""
    url = result.url.rstrip("/") + ".json"
    headers = {"User-Agent": "osint-pipeline/0.1 (research use)"}
    resp = requests.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
    resp.raise_for_status()
    payload = resp.json()

    parts = [result.text or ""]
    comment_children = payload[1]["data"]["children"]
    for child in comment_children:
        if child.get("kind") != "t1":
            continue
        body = child["data"].get("body", "")
        parts.append(body)
    return "\n---\n".join(parts)[:char_limit]


def _fetch_wikipedia_full(result: UnifiedResult, char_limit: int) -> str:
    """Full article extract via the Wikipedia REST API (not just the search snippet)."""
    title = result.title
    lang_url = result.url.split("/wiki/")[0]  # preserves whatever language subdomain was used
    api_url = f"{lang_url}/w/api.php"
    params = {
        "action": "query",
        "prop": "extracts",
        "explaintext": 1,
        "titles": title,
        "format": "json",
    }
    headers = {"User-Agent": "osint-pipeline/0.1 (research use)"}
    resp = requests.get(api_url, params=params, headers=headers, timeout=DEFAULT_TIMEOUT)
    resp.raise_for_status()
    pages = resp.json().get("query", {}).get("pages", {})
    for page in pages.values():
        return page.get("extract", "")[:char_limit]
    return ""


def _fetch_github_readme(result: UnifiedResult, char_limit: int) -> str:
    """README content via the GitHub API (returns base64, needs decoding)."""
    import base64
    full_name = result.title  # we stored "owner/repo" as title
    api_url = f"https://api.github.com/repos/{full_name}/readme"
    headers = {"Accept": "application/vnd.github+json"}
    resp = requests.get(api_url, headers=headers, timeout=DEFAULT_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    content = base64.b64decode(data.get("content", "")).decode("utf-8", errors="replace")
    return content[:char_limit]


def _fetch_hackernews_full(result: UnifiedResult, char_limit: int) -> str:
    """
    HN posts are usually just links -- 'full text' means the linked
    article's text, not anything HN itself hosts (except Ask/Show HN posts,
    which already have story_text populated at search time).
    """
    if result.text:  # Ask HN / Show HN text post, already have it
        return result.text[:char_limit]
    return _fetch_generic_page_text(result.url, char_limit)


def _fetch_stackexchange_full(result: UnifiedResult, char_limit: int) -> str:
    """Question body already fetched at search time; this just re-applies the limit."""
    return (result.text or "")[:char_limit]


def _fetch_mastodon_full(result: UnifiedResult, char_limit: int) -> str:
    """Mastodon status content is already complete at search time."""
    return (result.text or "")[:char_limit]


def _fetch_youtube_full(result: UnifiedResult, char_limit: int) -> str:
    """
    Full transcript via youtube_transcript_api -- same approach as the
    original YouTube pipeline. Falls back to the video description if no
    transcript is available (disabled, or none in a usable language).
    """
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import (
        TranscriptsDisabled,
        NoTranscriptFound,
        VideoUnavailable,
    )

    video_id = result.result_id
    ytt_api = YouTubeTranscriptApi()

    try:
        fetched = ytt_api.fetch(video_id, languages=["en"])
    except NoTranscriptFound:
        transcript_list = ytt_api.list(video_id)
        transcript = next(iter(transcript_list))
        fetched = transcript.fetch()
    except (TranscriptsDisabled, VideoUnavailable):
        # No transcript possible -- fall back to whatever description we already have
        return (result.text or "")[:char_limit]

    text = " ".join(snippet.text for snippet in fetched)
    return text[:char_limit]


_FETCHERS = {
    "reddit": _fetch_reddit_full,
    "wikipedia": _fetch_wikipedia_full,
    "github": _fetch_github_readme,
    "hackernews": _fetch_hackernews_full,
    "stackexchange": _fetch_stackexchange_full,
    "mastodon": _fetch_mastodon_full,
    "youtube": _fetch_youtube_full,
}


def fetch_full_text(result: UnifiedResult, char_limit: int = DEFAULT_CHAR_LIMIT) -> str:
    """
    Dispatch to the right per-source full-content fetcher.
    Returns plain text, truncated to char_limit. Raises on network failure --
    caller decides how to handle (this is meant for a small, already-selected
    batch, not a bulk loop that needs to silently degrade).
    """
    fetcher = _FETCHERS.get(result.source, lambda r, cl: _fetch_generic_page_text(r.url, cl))
    return fetcher(result, char_limit)


if __name__ == "__main__":
    # Quick manual test: run.py first, then point this at one result to confirm it works
    import json
    import sys
    from pathlib import Path

    results_path = Path(sys.argv[1] if len(sys.argv) > 1 else "results.json")
    data = json.loads(results_path.read_text(encoding="utf-8"))

    source = sys.argv[2] if len(sys.argv) > 2 else next(iter(data))
    index = int(sys.argv[3]) if len(sys.argv) > 3 else 0

    item = data[source][index]
    result = UnifiedResult(**item)

    print(f"Fetching full text for: {result.title} ({result.source})")
    full = fetch_full_text(result, char_limit=1500)
    print("\n--- FULL TEXT (truncated to 1500 chars) ---\n")
    print(full)