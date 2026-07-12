"""
Runner: fans a single query out across every available adapter and
aggregates results into one JSON file.

Usage:
    py -m pip install requests python-dotenv praw google-api-python-client
    py run.py "your search query"
    py run.py "your search query" --sources reddit,github,hackernews --limit 5
"""

from __future__ import annotations

import argparse
import concurrent.futures
import dataclasses
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")
from adapters import ALL_ADAPTERS
from core import UnifiedResult


def run_query(query: str, sources: list[str], limit: int = 10) -> dict[str, list[UnifiedResult]]:
    selected = {name: cls() for name, cls in ALL_ADAPTERS.items() if name in sources}

    skipped = [name for name, adapter in selected.items() if not adapter.is_configured()]
    for name in skipped:
        print(f"[skip] {name}: not configured (missing API key/credentials)", file=sys.stderr)
        del selected[name]

    results: dict[str, list[UnifiedResult]] = {}

    # Run adapters concurrently -- they're independent I/O-bound calls
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(selected) or 1) as pool:
        future_to_name = {
            pool.submit(adapter.search, query, limit): name
            for name, adapter in selected.items()
        }
        for future in concurrent.futures.as_completed(future_to_name):
            name = future_to_name[future]
            try:
                results[name] = future.result()
                errs = [r for r in results[name] if r.fetch_error]
                if errs:
                    print(f"[error] {name}: {errs[0].fetch_error}", file=sys.stderr)
                else:
                    print(f"[ok] {name}: {len(results[name])} results", file=sys.stderr)
            except Exception as e:
                print(f"[fail] {name}: {e}", file=sys.stderr)
                results[name] = []

    return results


def to_json(results: dict[str, list[UnifiedResult]]) -> str:
    plain = {
        name: [dataclasses.asdict(r) for r in items]
        for name, items in results.items()
    }
    return json.dumps(plain, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-source OSINT search pipeline")
    parser.add_argument("query", help="Search query")
    parser.add_argument(
        "--sources",
        default=",".join(ALL_ADAPTERS.keys()),
        help="Comma-separated list of sources to query (default: all)",
    )
    parser.add_argument("--limit", type=int, default=10, help="Max results per source")
    parser.add_argument("--out", default="results.json", help="Output JSON file path")
    args = parser.parse_args()

    sources = [s.strip() for s in args.sources.split(",") if s.strip()]
    unknown = set(sources) - set(ALL_ADAPTERS.keys())
    if unknown:
        print(f"Unknown sources: {unknown}. Available: {list(ALL_ADAPTERS.keys())}", file=sys.stderr)
        sys.exit(1)

    print(f"Querying {len(sources)} source(s) for: {args.query!r}", file=sys.stderr)
    results = run_query(args.query, sources, limit=args.limit)

    out_path = Path(args.out)
    out_path.write_text(to_json(results), encoding="utf-8")
    print(f"\nWrote results to {out_path.resolve()}", file=sys.stderr)

    total = sum(len(v) for v in results.values())
    print(f"Total results: {total} across {len(results)} sources", file=sys.stderr)