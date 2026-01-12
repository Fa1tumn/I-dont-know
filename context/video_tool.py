"""CLI tool to generate video copy (scripts/captions) using Deepseek"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# Prefer local imports
try:
    from generator import VideoGenerator
    from client import DeepseekClient
except Exception:
    from context.generator import VideoGenerator
    from context.client import DeepseekClient


class MockClient:
    def generate(self, prompt: str, **kwargs) -> str:
        # A simple predictable mock response that includes prompt summary
        brief_line = prompt.splitlines()[4] if len(prompt.splitlines()) > 4 else "(brief)"
        return f"[MOCK] 视频文案基于: {brief_line[:80]}..." 


def main():
    p = argparse.ArgumentParser(description="Generate video copy (script/caption) using Deepseek")
    p.add_argument("brief", help="Short brief describing the product or video idea")
    p.add_argument("-p", "--platform", default="short-video", help="Platform (e.g., douyin, tiktok, youtube)")
    p.add_argument("-f", "--format", dest="fmt", default="script", help="Format: script or caption")
    p.add_argument("-t", "--tone", help="Tone (e.g., energetic, professional)")
    p.add_argument("-l", "--length", help="Length (short, medium, long)")
    p.add_argument("-n", "--number", type=int, default=1, help="Number of variants to generate")
    p.add_argument("--out", help="Output file (JSON). If omitted, prints to stdout")
    p.add_argument("--mock", action="store_true", help="Run in mock/offline mode (no network)")
    args = p.parse_args()

    if args.mock:
        client = MockClient()
    else:
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise SystemExit("Please set DEEPSEEK_API_KEY environment variable or use --mock for offline testing.")
        client = DeepseekClient(api_key=api_key)

    gen = VideoGenerator(client)
    results = gen.generate(args.brief, platform=args.platform, fmt=args.fmt, tone=args.tone, length=args.length, n=args.number)

    if args.out:
        out_path = Path(args.out)
        out_path.write_text(json.dumps({"brief": args.brief, "results": results}, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Saved {len(results)} result(s) to {out_path}")
    else:
        print("\n--- Generated video copy ---\n")
        for i, r in enumerate(results, 1):
            print(f"[{i}] {r}\n")


if __name__ == "__main__":
    main()
