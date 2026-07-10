"""
YouTube Search + Transcript Pipeline
-------------------------------------
Given a search query, finds relevant YouTube videos and fetches their
transcripts.

Install dependencies first:
    pip install yt-dlp youtube-transcript-api

Usage:
    python youtube_pipeline.py "your search query" --max-results 5
"""

import argparse
import json
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

from yt_dlp import YoutubeDL
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)


@dataclass
class VideoResult:
    video_id: str
    title: str
    url: str
    channel: Optional[str] = None
    duration: Optional[int] = None
    transcript: Optional[str] = None
    transcript_error: Optional[str] = None


def search_youtube(query: str, max_results: int = 5) -> list[VideoResult]:
    """
    Search YouTube using yt-dlp (no API key required) and return
    basic metadata for the top N results.
    """
    search_query = f"ytsearch{max_results}:{query}"

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,  # don't resolve full info yet, just listing
        "skip_download": True,
    }

    results: list[VideoResult] = []

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(search_query, download=False)
        entries = info.get("entries", []) if info else []

        for entry in entries:
            if not entry:
                continue
            video_id = entry.get("id")
            title = entry.get("title", "Unknown title")
            channel = entry.get("channel") or entry.get("uploader")
            duration = entry.get("duration")
            url = f"https://www.youtube.com/watch?v={video_id}"

            results.append(
                VideoResult(
                    video_id=video_id,
                    title=title,
                    url=url,
                    channel=channel,
                    duration=duration,
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
    query: str, max_results: int = 5, languages: list[str] = None
) -> list[VideoResult]:
    """
    Full pipeline: search -> fetch transcripts -> return enriched results.
    """
    print(f"Searching YouTube for: '{query}' (top {max_results})...", file=sys.stderr)
    videos = search_youtube(query, max_results=max_results)

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
    results = run_pipeline(
        query="how does photosynthesis work",
        max_results=3,
        languages=["en"],
    )
 
    for video in results:
        print("\n" + "=" * 80)
        print(f"Title:   {video.title}")
        print(f"URL:     {video.url}")
        print(f"Channel: {video.channel}")
        if video.transcript:
            print(f"\nTranscript preview:\n{video.transcript[:500]}...")
        else:
            print(f"\nTranscript unavailable: {video.transcript_error}")
 


