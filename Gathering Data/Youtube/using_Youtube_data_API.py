"""
YouTube Search (Data API v3) + Transcript Pipeline
----------------------------------------------------
Given a search query, finds relevant YouTube videos using the official
YouTube Data API v3, then fetches their transcripts.

Install dependencies first:
    pip install google-api-python-client youtube-transcript-api

You need a YouTube Data API v3 key:
    1. Go to https://console.cloud.google.com/
    2. Create/select a project
    3. Enable "YouTube Data API v3"
    4. Create credentials -> API key

Usage:
    export YOUTUBE_API_KEY="your_key_here"
    python youtube_pipeline_api.py "your search query" --max-results 5

    # or pass the key directly
    python youtube_pipeline_api.py "your search query" --api-key YOUR_KEY
"""

import os
import sys
from dataclasses import dataclass
from typing import Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)

from dotenv import load_dotenv
load_dotenv()


@dataclass
class VideoResult:
    video_id: str
    title: str
    url: str
    channel: Optional[str] = None
    published_at: Optional[str] = None
    description: Optional[str] = None
    transcript: Optional[str] = None
    transcript_error: Optional[str] = None


def search_youtube(
    query: str, api_key: str, max_results: int = 5, order: str = "relevance"
) -> list[VideoResult]:
    """
    Search YouTube using the official Data API v3 search.list endpoint.
    Costs 100 quota units per call (default daily quota is 10,000 units).
    """
    youtube = build("youtube", "v3", developerKey=api_key)

    try:
        response = (
            youtube.search()
            .list(
                q=query,
                part="snippet",
                type="video",
                maxResults=max_results,
                order=order,  # relevance, date, rating, viewCount, title
            )
            .execute()
        )
    except HttpError as e:
        print(f"YouTube API error: {e}", file=sys.stderr)
        raise

    results: list[VideoResult] = []
    for item in response.get("items", []):
        video_id = item["id"]["videoId"]
        snippet = item["snippet"]

        results.append(
            VideoResult(
                video_id=video_id,
                title=snippet.get("title", "Unknown title"),
                url=f"https://www.youtube.com/watch?v={video_id}",
                channel=snippet.get("channelTitle"),
                published_at=snippet.get("publishedAt"),
                description=snippet.get("description"),
            )
        )

    return results


def fetch_transcript(video_id: str, languages: list[str] = None) -> str:
    """
    Fetch and flatten the transcript for a given video ID.
    Uses the v1.0+ instance-based API.
    """
    if languages is None:
        languages = ["en"]

    ytt_api = YouTubeTranscriptApi()

    try:
        fetched_transcript = ytt_api.fetch(video_id, languages=languages)
    except NoTranscriptFound:
        # Fall back to whatever transcript is available, in any language
        transcript_list = ytt_api.list(video_id)
        transcript = next(iter(transcript_list))
        fetched_transcript = transcript.fetch()

    text = " ".join(snippet.text for snippet in fetched_transcript)
    return text


def run_pipeline(
    query: str,
    api_key: str,
    max_results: int = 5,
    languages: list[str] = None,
    order: str = "relevance",
) -> list[VideoResult]:
    """
    Full pipeline: search (Data API v3) -> fetch transcripts -> enriched results.
    """
    print(f"Searching YouTube for: '{query}' (top {max_results}, order={order})...", file=sys.stderr)
    videos = search_youtube(query, api_key=api_key, max_results=max_results, order=order)

    for video in videos:
        print(f"Fetching transcript for: {video.title} ({video.video_id})", file=sys.stderr)
        try:
            video.transcript = fetch_transcript(video.video_id, languages=languages)
        except TranscriptsDisabled:
            video.transcript_error = "Transcripts are disabled for this video."
        except NoTranscriptFound:
            video.transcript_error = "No transcript found in the requested language(s)."
        except VideoUnavailable:
            video.transcript_error = "Video is unavailable."
        except Exception as e:  # noqa: BLE001 - surface any unexpected error per-video
            video.transcript_error = f"Unexpected error: {e}"

    return videos


if __name__ == "__main__":
    API_KEY = os.environ.get("YOUTUBE_API_KEY")
 
    results = run_pipeline(
        query="how does photosynthesis work",
        api_key=API_KEY,
        max_results=3,
        languages=["en"],
        order="relevance",
    )
 
    for video in results:
        print("\n" + "=" * 80)
        print(f"Title:     {video.title}")
        print(f"URL:       {video.url}")
        print(f"Channel:   {video.channel}")
        if video.transcript:
            print(f"\nTranscript preview:\n{video.transcript[:500]}...")
        else:
            print(f"\nTranscript unavailable: {video.transcript_error}")
