"""CLI tool to generate video copy (scripts/captions) using Deepseek"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from datetime import datetime

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
    def generate(self, prompt: str, n: int = 1, **kwargs):
        # Return string if n==1 else list of strings; include platform hint if present in prompt
        brief_line = prompt.splitlines()[4] if len(prompt.splitlines()) > 4 else "(brief)"
        base = f"[MOCK] 视频文案基于: {brief_line[:80]}..."
        if n is None or n <= 1:
            return base
        return [f"{base} (变体 {i+1})" for i in range(n)]


def main():
    p = argparse.ArgumentParser(description="Generate video copy (script/caption) using Deepseek")
    p.add_argument("brief", help="Short brief describing the product or video idea")
    p.add_argument("-p", "--platform", default="short-video", help="Platform (e.g., douyin, tiktok, youtube)")
    p.add_argument("-f", "--format", dest="fmt", default="script", help="Format: script or caption")
    p.add_argument("-t", "--tone", help="Tone (e.g., energetic, professional)")
    p.add_argument("-l", "--length", help="Length (short, medium, long)")
    p.add_argument("-n", "--number", type=int, default=1, help="Number of variants to generate")
    p.add_argument("-s", "--similarity", type=int, default=100, help="Similarity percentage to original brief (0-100)")
    p.add_argument("--out", help="Output file (JSON). If omitted, prints to stdout")
    p.add_argument("--mock", action="store_true", help="Run in mock/offline mode (no network)")
    p.add_argument("--debug", action="store_true", help="Show debug info (provider, model, masked API key)")
    p.add_argument("--log-pretty", action="store_true", help="Write pretty JSON into the log file (one object per line by default)")
    args = p.parse_args()

    if args.mock:
        client = MockClient()
        if args.debug:
            print(f"Provider: Zhipu/BigModel (mock)\nPlatform: {args.platform}\nAPI key: (mock)")
    else:
        api_key = os.getenv("ZHIPU_API_KEY") or os.getenv("BIGMODEL_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise SystemExit("Please set ZHIPU_API_KEY environment variable or use --mock for offline testing.")
        if args.debug:
            masked = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "****"
            print(f"Provider: Zhipu/BigModel\nPlatform: {args.platform}\nAPI key (masked): {masked}")
        client = DeepseekClient(api_key=api_key)

    gen = VideoGenerator(client)
    try:
        results = gen.generate(args.brief, platform=args.platform, fmt=args.fmt, tone=args.tone, length=args.length, n=args.number)
    except Exception as e:
        print(f"网络或API错误: {e}\n提示：可以使用 --mock 进行本地测试，或检查网络/API Key 设置。")
        raise

    # Append a JSON log entry to context_generated.log in the same folder as this script
    log_path = Path(__file__).parent / "context_generated.log"

    # Try to use structured JSON if the generated result is already JSON matching expected schema
    def try_parse_result_as_schema(text: str):
        try:
            obj = json.loads(text)
            if isinstance(obj, dict) and "script/caption" in obj:
                return obj
        except Exception:
            pass
        return None

    body = None
    # If there is exactly one result and it's JSON with the desired schema, use it
    if len(results) == 1:
        parsed = try_parse_result_as_schema(results[0])
        if parsed:
            body = parsed

    # Otherwise build a schema-wrapped object
    if body is None:
        body = {
            "script/caption": [],
            "title": args.brief,
            "tags": [],
        }
        for r in results:
            # try to extract tags from inline hashtags
            tags = [t for t in r.split() if t.startswith("#")]
            if tags:
                body["tags"].extend(tags)
            body["script/caption"].append({
                "time": "0-60s",
                "title": "",
                "caption": r,
            })
        # dedupe tags
        body["tags"] = list(dict.fromkeys(body["tags"]))

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "brief": args.brief,
        "platform": args.platform,
        "format": args.fmt,
        "tone": args.tone,
        "length": args.length,
        "number": args.number,
        "data": body,
    }

    try:
        with log_path.open("a", encoding="utf-8") as f:
            if args.log_pretty:
                f.write(json.dumps(log_entry, ensure_ascii=False, indent=2) + "\n")
            else:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        print(f"Appended {len(results)} result(s) to {log_path}")
    except Exception as e:
        print(f"Warning: 无法写入日志文件 {log_path}: {e}")

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
