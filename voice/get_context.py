"""Extract time/content pairs from context/context_generated.log

Usage:
  python voice/get_context.py --log ../context/context_generated.log --out extracted_captions.json --format json

The script handles several shapes found in the log:
 - entries where `data["script/caption"]` is a list of blocks with `time` and `caption` or `content`
 - entries where `results` contains a fenced JSON string (```json ... ```) with `script/caption`
 - entries where a block's caption is itself a fenced JSON with `captions` array containing `time` and `content`

Output is a JSON array of objects: {"timestamp":..., "time":..., "content":..., "title":..., "source":"<line>"}
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

CODE_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", flags=re.DOTALL)


def load_log_lines(path: Path) -> List[Dict[str, Any]]:
    entries = []
    with path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                entries.append(obj)
            except Exception:
                # try to salvage if the line contains JSON somewhere
                m = CODE_FENCE_RE.search(line)
                if m:
                    try:
                        obj = json.loads(m.group(1))
                        entries.append(obj)
                    except Exception:
                        print(f"Warning: failed to parse JSON on line {i}")
                else:
                    print(f"Warning: invalid JSON line {i}, skipping")
    return entries


def extract_fenced_json(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    m = CODE_FENCE_RE.search(text)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except Exception:
        return None


def strip_code_fence(text: str) -> str:
    # remove triple backticks if present
    return re.sub(r"```(?:json)?\s*|\s*```", "", text).strip()


def extract_blocks_from_script_caption(block: Dict[str, Any]) -> List[Dict[str, str]]:
    out = []
    # block may have 'time' and either 'caption' or 'content'
    time = block.get("time") or block.get("time_range") or ""
    title = block.get("title") or ""
    # caption may be a fenced json string
    if "caption" in block and isinstance(block["caption"], str):
        caption = block["caption"].strip()
        # If caption contains a fenced JSON with captions array, parse it
        inner = extract_fenced_json(caption)
        if inner and isinstance(inner, dict) and "captions" in inner:
            for c in inner["captions"]:
                out.append({"time": c.get("time", ""), "content": c.get("content", c.get("caption", "")), "title": c.get("title", "")})
            return out
        # otherwise treat caption as plain text
        out.append({"time": time, "content": strip_code_fence(caption), "title": title})
        return out

    if "content" in block and isinstance(block["content"], str):
        out.append({"time": time, "content": strip_code_fence(block["content"]), "title": title})
        return out

    # unknown shape: try to stringify
    out.append({"time": time, "content": strip_code_fence(json.dumps(block, ensure_ascii=False)), "title": title})
    return out


def extract_from_entry(entry: Dict[str, Any]) -> List[Dict[str, Any]]:
    found: List[Dict[str, Any]] = []
    ts = entry.get("timestamp")

    # 1) If there's a `data` with `script/caption`
    data = entry.get("data")
    if data and isinstance(data, dict):
        sc = data.get("script/caption")
        if isinstance(sc, list):
            for block in sc:
                blocks = extract_blocks_from_script_caption(block)
                for b in blocks:
                    found.append({"timestamp": ts, "time": b.get("time", ""), "content": b.get("content", ""), "title": b.get("title", "")})
            return found

    # 2) If there's `results` which may contain fenced JSON
    results = entry.get("results")
    if isinstance(results, list):
        for r in results:
            if not isinstance(r, str):
                continue
            inner = extract_fenced_json(r)
            if inner:
                # inner may have script/caption
                sc = inner.get("script/caption") or inner.get("captions")
                if isinstance(sc, list):
                    # if items have caption/content
                    for item in sc:
                        if isinstance(item, dict):
                            content = item.get("caption") or item.get("content") or ""
                            time = item.get("time") or ""
                            title = item.get("title") or ""
                            found.append({"timestamp": ts, "time": time, "content": strip_code_fence(str(content)), "title": title})
                    continue
            # fallback: treat r as a plain caption
            text = strip_code_fence(r)
            found.append({"timestamp": ts, "time": "", "content": text, "title": ""})
        return found

    # 3) fallback: try to find any fenced JSON inside other fields
    for k, v in entry.items():
        if isinstance(v, str):
            inner = extract_fenced_json(v)
            if inner and isinstance(inner, dict):
                sc = inner.get("script/caption") or inner.get("captions")
                if isinstance(sc, list):
                    for item in sc:
                        time = item.get("time") or ""
                        content = item.get("caption") or item.get("content") or ""
                        title = item.get("title") or ""
                        found.append({"timestamp": ts, "time": time, "content": strip_code_fence(str(content)), "title": title})
    return found


def dedupe_and_flatten(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    out: List[Dict[str, Any]] = []
    for it in items:
        key = (it.get("timestamp"), it.get("time"), it.get("content"))
        if key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out


def write_json(path: Path, items: List[Dict[str, Any]]):
    path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, items: List[Dict[str, Any]]):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "time", "title", "content"])
        for i in items:
            writer.writerow([i.get("timestamp", ""), i.get("time", ""), i.get("title", ""), i.get("content", "")])


def get_content_json():
    p = argparse.ArgumentParser(description="Extract time/content captions from context_generated.log")
    p.add_argument("--log", default=Path(__file__).parent.parent / "context" / "context_generated.log", help="Path to context/context_generated.log")
    p.add_argument("--out", default=None, help="Output file (json or csv). If omitted prints to stdout")
    p.add_argument("--format", choices=["json", "csv"], default="json", help="Output format when writing to a file")
    args = p.parse_args()

    log_path = Path(args.log)
    if not log_path.exists():
        raise SystemExit(f"Log file not found: {log_path}")

    entries = load_log_lines(log_path)

    all_items: List[Dict[str, Any]] = []
    for e in entries:
        items = extract_from_entry(e)
        all_items.extend(items)

    all_items = dedupe_and_flatten(all_items)

    if args.out:
        out_path = Path(args.out)
        if args.format == "json":
            write_json(out_path, all_items)
        else:
            write_csv(out_path, all_items)
        print(f"Wrote {len(all_items)} captions to {out_path}")
    else:
        print(json.dumps(all_items, ensure_ascii=False, indent=2))

    return all_items
if __name__ == "__main__":
    print(get_content_json())
