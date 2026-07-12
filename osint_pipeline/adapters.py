"""
Adapters for individual sources. Each wraps a free, ToS-compliant API.

Design note: every adapter degrades gracefully. If credentials are missing
or a request fails, it returns an empty list (or a single UnifiedResult
with fetch_error set) rather than raising -- the runner treats sources
as independent and keeps going.
"""

from __future__ import annotations

import os
import time
from typing import Optional

import requests

from core import SourceAdapter, UnifiedResult, now_iso


DEFAULT_TIMEOUT = 10.0


# ---------------------------------------------------------------------------
# Hacker News -- fully free, no key, Firebase-backed
# ---------------------------------------------------------------------------

class HackerNewsAdapter(SourceAdapter):
    name = "hackernews"

    SEARCH_URL = "https://hn.algolia.com/api/v1/search"

    def search(self, query: str, limit: int = 10) -> list[UnifiedResult]:
        # HN's own Firebase API has no text search; the community-run
        # Algolia-backed search API is the standard free way to query it.
        params = {"query": query, "tags": "story", "hitsPerPage": limit}
        try:
            resp = requests.get(self.SEARCH_URL, params=params, timeout=DEFAULT_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            return [UnifiedResult(source=self.name, result_id="", title="", url="", fetch_error=str(e))]

        results = []
        for hit in data.get("hits", []):
            results.append(
                UnifiedResult(
                    source=self.name,
                    result_id=hit.get("objectID", ""),
                    title=hit.get("title") or hit.get("story_title") or "(no title)",
                    url=hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                    author=hit.get("author"),
                    created_at=hit.get("created_at"),
                    score=hit.get("points"),
                    text=hit.get("story_text"),
                    extra={"num_comments": hit.get("num_comments")},
                )
            )
        return results


# ---------------------------------------------------------------------------
# Stack Exchange (Stack Overflow etc.) -- free, generous, no key required
# for low volume (but a free registered key raises your quota)
# ---------------------------------------------------------------------------

class StackExchangeAdapter(SourceAdapter):
    name = "stackexchange"

    SEARCH_URL = "https://api.stackexchange.com/2.3/search/advanced"

    def __init__(self, site: str = "stackoverflow"):
        self.site = site
        self.api_key = os.environ.get("STACKEXCHANGE_API_KEY")  # optional

    def search(self, query: str, limit: int = 10) -> list[UnifiedResult]:
        params = {
            "q": query,
            "site": self.site,
            "pagesize": limit,
            "order": "desc",
            "sort": "relevance",
            # withbody filter includes the question's full body text in the
            # same response, so we get a relevance-indicator for free
            # instead of a second request per question.
            "filter": "withbody",
        }
        if self.api_key:
            params["key"] = self.api_key

        try:
            resp = requests.get(self.SEARCH_URL, params=params, timeout=DEFAULT_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            return [UnifiedResult(source=self.name, result_id="", title="", url="", fetch_error=str(e))]

        results = []
        for item in data.get("items", []):
            results.append(
                UnifiedResult(
                    source=self.name,
                    result_id=str(item.get("question_id")),
                    title=_strip_html(item.get("title", "")),
                    url=item.get("link", ""),
                    author=item.get("owner", {}).get("display_name"),
                    created_at=str(item.get("creation_date")),
                    score=item.get("score"),
                    text=_strip_html(item.get("body", "")),
                    extra={
                        "answer_count": item.get("answer_count"),
                        "is_answered": item.get("is_answered"),
                        "tags": item.get("tags"),
                    },
                )
            )
        return results


# ---------------------------------------------------------------------------
# Wikipedia -- fully free REST API, no key
# ---------------------------------------------------------------------------

class WikipediaAdapter(SourceAdapter):
    name = "wikipedia"

    def __init__(self, lang: str = "en"):
        self.search_url = f"https://{lang}.wikipedia.org/w/api.php"

    def search(self, query: str, limit: int = 10) -> list[UnifiedResult]:
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "srlimit": limit,
        }
        headers = {"User-Agent": "osint-pipeline/0.1 (research use)"}

        try:
            resp = requests.get(self.search_url, params=params, headers=headers, timeout=DEFAULT_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            return [UnifiedResult(source=self.name, result_id="", title="", url="", fetch_error=str(e))]

        results = []
        base = self.search_url.replace("/w/api.php", "/wiki/")
        for item in data.get("query", {}).get("search", []):
            title = item.get("title", "")
            results.append(
                UnifiedResult(
                    source=self.name,
                    result_id=str(item.get("pageid")),
                    title=title,
                    url=base + title.replace(" ", "_"),
                    created_at=item.get("timestamp"),
                    text=_strip_html(item.get("snippet", "")),
                    extra={"wordcount": item.get("wordcount")},
                )
            )
        return results


def _strip_html(s: str) -> str:
    import html
    import re
    text = re.sub(r"<[^>]+>", "", s)
    return html.unescape(text)


# ---------------------------------------------------------------------------
# GitHub -- free REST API, generous unauthenticated limits, higher with a
# free personal access token
# ---------------------------------------------------------------------------

class GitHubAdapter(SourceAdapter):
    name = "github"

    SEARCH_URL = "https://api.github.com/search/repositories"

    def __init__(self):
        self.token = os.environ.get("GITHUB_TOKEN")  # optional, raises rate limit

    def search(self, query: str, limit: int = 10) -> list[UnifiedResult]:
        params = {"q": query, "per_page": limit, "sort": "stars", "order": "desc"}
        headers = {"Accept": "application/vnd.github+json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        try:
            resp = requests.get(self.SEARCH_URL, params=params, headers=headers, timeout=DEFAULT_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            return [UnifiedResult(source=self.name, result_id="", title="", url="", fetch_error=str(e))]

        results = []
        for item in data.get("items", []):
            results.append(
                UnifiedResult(
                    source=self.name,
                    result_id=str(item.get("id")),
                    title=item.get("full_name", ""),
                    url=item.get("html_url", ""),
                    author=item.get("owner", {}).get("login"),
                    created_at=item.get("created_at"),
                    score=item.get("stargazers_count"),
                    text=item.get("description"),
                    extra={"language": item.get("language"), "forks": item.get("forks_count")},
                )
            )
        return results


# ---------------------------------------------------------------------------
# Mastodon -- pick a public instance; federated search is instance-scoped
# ---------------------------------------------------------------------------

class MastodonAdapter(SourceAdapter):
    name = "mastodon"

    def __init__(self, instance: str = "mastodon.social"):
        self.search_url = f"https://{instance}/api/v2/search"

    def search(self, query: str, limit: int = 10) -> list[UnifiedResult]:
        params = {"q": query, "type": "statuses", "limit": limit}
        try:
            resp = requests.get(self.search_url, params=params, timeout=DEFAULT_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            return [UnifiedResult(source=self.name, result_id="", title="", url="", fetch_error=str(e))]

        results = []
        for status in data.get("statuses", []):
            account = status.get("account", {})
            results.append(
                UnifiedResult(
                    source=self.name,
                    result_id=str(status.get("id")),
                    title=_strip_html(status.get("content", ""))[:80],
                    url=status.get("url", ""),
                    author=account.get("acct"),
                    created_at=status.get("created_at"),
                    score=status.get("favourites_count"),
                    text=_strip_html(status.get("content", "")),
                    extra={"reblogs": status.get("reblogs_count")},
                )
            )
        return results


# ---------------------------------------------------------------------------
# Reddit -- free .json endpoint, PRAW fallback (needs free registered app)
# ---------------------------------------------------------------------------

class RedditAdapter(SourceAdapter):
    name = "reddit"

    def __init__(self):
        self.user_agent = os.environ.get("REDDIT_USER_AGENT", "osint-pipeline/0.1")
        self.client_id = os.environ.get("REDDIT_CLIENT_ID")
        self.client_secret = os.environ.get("REDDIT_CLIENT_SECRET")

    def search(self, query: str, limit: int = 10) -> list[UnifiedResult]:
        results = self._search_json(query, limit)
        if results and results[0].fetch_error:
            if self.client_id and self.client_secret:
                return self._search_praw(query, limit)
        return results

    def _search_json(self, query: str, limit: int) -> list[UnifiedResult]:
        url = "https://www.reddit.com/search.json"
        params = {"q": query, "limit": limit, "sort": "relevance"}
        headers = {"User-Agent": self.user_agent}
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=DEFAULT_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            return [UnifiedResult(source=self.name, result_id="", title="", url="", fetch_error=str(e))]

        results = []
        for child in data.get("data", {}).get("children", []):
            d = child.get("data", {})
            results.append(
                UnifiedResult(
                    source=self.name,
                    result_id=d.get("id", ""),
                    title=d.get("title", ""),
                    url="https://www.reddit.com" + d.get("permalink", ""),
                    author=d.get("author"),
                    created_at=str(d.get("created_utc")),
                    score=d.get("score"),
                    text=d.get("selftext"),
                    extra={"subreddit": d.get("subreddit"), "num_comments": d.get("num_comments")},
                )
            )
        return results

    def _search_praw(self, query: str, limit: int) -> list[UnifiedResult]:
        try:
            import praw
        except ImportError:
            return [UnifiedResult(source=self.name, result_id="", title="", url="",
                                   fetch_error="praw not installed")]
        try:
            reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent,
            )
            results = []
            for submission in reddit.subreddit("all").search(query, limit=limit):
                results.append(
                    UnifiedResult(
                        source=self.name,
                        result_id=submission.id,
                        title=submission.title,
                        url=f"https://www.reddit.com{submission.permalink}",
                        author=str(submission.author) if submission.author else None,
                        created_at=str(submission.created_utc),
                        score=submission.score,
                        text=submission.selftext,
                        extra={"subreddit": str(submission.subreddit)},
                    )
                )
            return results
        except Exception as e:
            return [UnifiedResult(source=self.name, result_id="", title="", url="", fetch_error=str(e))]

    def is_configured(self) -> bool:
        return True  # json path always attempts; praw is optional bonus


# ---------------------------------------------------------------------------
# YouTube -- free Data API v3 (needs a free Google Cloud API key)
# ---------------------------------------------------------------------------

class YouTubeAdapter(SourceAdapter):
    name = "youtube"

    def __init__(self):
        self.api_key = os.environ.get("YOUTUBE_API_KEY")

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def search(self, query: str, limit: int = 10) -> list[UnifiedResult]:
        if not self.api_key:
            return [UnifiedResult(source=self.name, result_id="", title="", url="",
                                   fetch_error="YOUTUBE_API_KEY not set")]
        try:
            from googleapiclient.discovery import build
            youtube = build("youtube", "v3", developerKey=self.api_key)
            resp = youtube.search().list(
                q=query, part="snippet", type="video", maxResults=limit
            ).execute()
        except Exception as e:
            return [UnifiedResult(source=self.name, result_id="", title="", url="", fetch_error=str(e))]

        results = []
        for item in resp.get("items", []):
            vid = item["id"]["videoId"]
            snippet = item["snippet"]
            results.append(
                UnifiedResult(
                    source=self.name,
                    result_id=vid,
                    title=snippet.get("title", ""),
                    url=f"https://www.youtube.com/watch?v={vid}",
                    author=snippet.get("channelTitle"),
                    created_at=snippet.get("publishedAt"),
                    text=snippet.get("description"),
                )
            )
        return results


# ---------------------------------------------------------------------------
# Bluesky -- fully open AT Protocol public API, no auth needed for search
# ---------------------------------------------------------------------------

class BlueskyAdapter(SourceAdapter):
    name = "bluesky"

    SEARCH_URL = "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts"

    def search(self, query: str, limit: int = 10) -> list[UnifiedResult]:
        params = {"q": query, "limit": limit}
        try:
            resp = requests.get(self.SEARCH_URL, params=params, timeout=DEFAULT_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            return [UnifiedResult(source=self.name, result_id="", title="", url="", fetch_error=str(e))]

        results = []
        for post in data.get("posts", []):
            author = post.get("author", {})
            record = post.get("record", {})
            handle = author.get("handle", "")
            # Bluesky post URLs are constructed from the handle + the post's
            # own rkey (last segment of its at:// URI), there's no direct
            # https URL field in the API response.
            uri = post.get("uri", "")
            rkey = uri.rsplit("/", 1)[-1] if uri else ""
            text = record.get("text", "")

            results.append(
                UnifiedResult(
                    source=self.name,
                    result_id=uri,
                    title=text[:80] if text else "(no text)",
                    url=f"https://bsky.app/profile/{handle}/post/{rkey}" if handle and rkey else "",
                    author=handle,
                    created_at=record.get("createdAt"),
                    score=post.get("likeCount"),
                    text=text,
                    extra={
                        "reposts": post.get("repostCount"),
                        "replies": post.get("replyCount"),
                    },
                )
            )
        return results


# ---------------------------------------------------------------------------
# Lemmy -- federated, Reddit-like. Free REST API per instance (no key),
# same federation caveat as Mastodon: one instance's search != all of Lemmy.
# ---------------------------------------------------------------------------

class LemmyAdapter(SourceAdapter):
    name = "lemmy"

    def __init__(self, instance: str = "lemmy.world"):
        self.search_url = f"https://{instance}/api/v3/search"

    def search(self, query: str, limit: int = 10) -> list[UnifiedResult]:
        params = {
            "q": query,
            "type_": "Posts",
            "sort": "TopAll",
            "limit": limit,
        }
        headers = {"User-Agent": "osint-pipeline/0.1 (research use)"}
        try:
            resp = requests.get(self.search_url, params=params, headers=headers, timeout=DEFAULT_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            return [UnifiedResult(source=self.name, result_id="", title="", url="", fetch_error=str(e))]

        results = []
        for item in data.get("posts", []):
            post = item.get("post", {})
            counts = item.get("counts", {})
            creator = item.get("creator", {})
            community = item.get("community", {})

            results.append(
                UnifiedResult(
                    source=self.name,
                    result_id=str(post.get("id")),
                    title=post.get("name", ""),
                    url=post.get("ap_id", ""),  # ActivityPub id doubles as the canonical link
                    author=creator.get("name"),
                    created_at=post.get("published"),
                    score=counts.get("score"),
                    text=post.get("body"),
                    extra={
                        "community": community.get("name"),
                        "num_comments": counts.get("comments"),
                    },
                )
            )
        return results


ALL_ADAPTERS = {
    "hackernews": HackerNewsAdapter,
    "stackexchange": StackExchangeAdapter,
    "wikipedia": WikipediaAdapter,
    "github": GitHubAdapter,
    "mastodon": MastodonAdapter,
    "reddit": RedditAdapter,
    "youtube": YouTubeAdapter,
    "bluesky": BlueskyAdapter,
    "lemmy": LemmyAdapter,
}