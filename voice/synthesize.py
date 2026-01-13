"""Synthesize captions to WAV using local CosyVoice API

Usage examples:
  # default voice (中文女)
  python synthesize.py --input ../context_extracted.json --mode tts --voice "中文女" --server http://127.0.0.1:9933 --out-dir ../audio_out

  # clone voice (same-language clone): copy local ref.wav into server repo and call /clone_eq
  python synthesize.py --input ../context_extracted.json --mode clone_eq --reference-audio ../ref.wav --reference-text "参考文本" --server-repo ../cosyvoice-api --server http://127.0.0.1:9933 --out-dir ../audio_out

Behavior:
 - If --input is omitted, the script runs the extractor at ../voice/get_context.py to extract from ../context/context_generated.log
 - Mode 'tts' uses built-in voices via /v1/audio/speech
 - Mode 'clone_eq' (same-language clone) copies --reference-audio into the server repo (if provided) and calls /clone_eq with text and reference_audio filename
 - Mode 'clone_mul' (cross-lingual) behaves similarly but calls /clone
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Dict, List

import requests


def run_extractor_and_load(path_to_extractor: Path) -> List[Dict]:
    # Run the extractor script and capture JSON output
    import subprocess
    out = subprocess.check_output([sys.executable, str(path_to_extractor)], cwd=str(path_to_extractor.parent), text=True)
    return json.loads(out)


def load_input(input_path: Path):
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    return json.loads(input_path.read_text(encoding="utf-8"))


def ensure_outdir(p: Path):
    p.mkdir(parents=True, exist_ok=True)


def call_tts(server: str, text: str, voice: str, outpath: Path, speed: float = 1.0):
    url = f"{server.rstrip('/')}/v1/audio/speech"
    payload = {"input": text, "voice": voice, "speed": speed}
    r = requests.post(url, json=payload, stream=True, timeout=1800)
    r.raise_for_status()
    with open(outpath, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)


def call_clone(server: str, mode: str, text: str, reference_filename: str, reference_text: str, outpath: Path, server_repo: Path = None):
    # mode: 'clone_eq' or 'clone' (clone_mul)
    url = f"{server.rstrip('/')}/{mode}"

    # The API expects reference_audio to be a filename relative to api.py
    data = {"text": text}
    files = None
    if mode == 'clone_eq' and reference_text:
        data["reference_text"] = reference_text

    # If server_repo provided, copy file into server repo folder so the server can find it by name
    # Otherwise, we still allow sending reference_audio as base64 by sending a 'reference_audio' field if the API supports it.
    data["reference_audio"] = reference_filename

    r = requests.post(url, data=data, timeout=1800, stream=True)
    r.raise_for_status()
    with open(outpath, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", help="Extracted captions JSON file (array of {timestamp,time,content,title})")
    p.add_argument("--extractor", help="Path to extractor script relative to repo (default: ../voice/get_context.py)", default=Path(__file__).parent / "get_context.py")
    p.add_argument("--server", help="CosyVoice server base URL", default="http://127.0.0.1:9933")
    p.add_argument("--mode", choices=["tts", "clone_eq", "clone"], default="tts", help="Synthesis mode")
    p.add_argument("--voice", default="中文女", help="Role for tts mode")
    p.add_argument("--reference-audio", help="Local path to reference WAV for clone modes")
    p.add_argument("--reference-text", help="Reference text for same-language clone (clone_eq)")
    p.add_argument("--server-repo", help="Path to cosyvoice-api repo (used to copy reference audio in for cloning)")
    p.add_argument("--out-dir", help="Where to save WAV files", default=Path(__file__).parent.parent / "audio_out")
    p.add_argument("--speed", type=float, default=1.0, help="Speech speed")
    args = p.parse_args()

    out_dir = Path(args.out_dir)
    ensure_outdir(out_dir)

    # Load or extract captions
    items = []
    if args.input:
        items = load_input(Path(args.input))
    else:
        extractor = Path(args.extractor)
        if not extractor.exists():
            # fallback to relative path inside voice/
            extractor = Path(__file__).parent / "get_context.py"
        items = run_extractor_and_load(extractor)

    if not items:
        print("No captions found to synthesize.")
        return

    # If cloning and reference audio provided and server_repo provided, copy file
    reference_filename = None
    if args.mode in ("clone_eq", "clone"):
        if not args.reference_audio:
            raise SystemExit("--reference-audio is required for clone modes")
        ref_path = Path(args.reference_audio)
        if not ref_path.exists():
            raise FileNotFoundError(f"Reference audio not found: {ref_path}")
        if args.server_repo:
            repo_path = Path(args.server_repo)
            if not repo_path.exists():
                raise FileNotFoundError(f"server repo not found: {repo_path}")
            # copy into server repo folder
            dest = repo_path / ref_path.name
            shutil.copy2(ref_path, dest)
            reference_filename = ref_path.name
            print(f"Copied reference audio to server repo: {dest}")
        else:
            # If server repo not provided, assume reference_filename is accessible to server as provided path
            reference_filename = str(ref_path)

    # Call API per caption
    for i, it in enumerate(items, 1):
        time_seg = it.get("time", "")
        content = it.get("content") or it.get("caption") or ""
        title = it.get("title", "")
        safe_time = time_seg.replace(" ", "_").replace("/", "-")[:40]
        outname = f"{i:02d}-{safe_time}.wav" if safe_time else f"{i:02d}.wav"
        outpath = out_dir / outname
        print(f"Synthesizing [{i}] time={time_seg} title={title} -> {outpath}")
        try:
            if args.mode == 'tts':
                call_tts(args.server, content, args.voice, outpath, speed=args.speed)
            else:
                call_clone(args.server, args.mode, content, reference_filename, args.reference_text or "", outpath, server_repo=Path(args.server_repo) if args.server_repo else None)
        except requests.HTTPError as e:
            print(f"HTTP error for item {i}: {e} - response: {getattr(e.response, 'text', '')}")
        except Exception as e:
            print(f"Error synthesizing item {i}: {e}")

    print(f"Done. Files saved to {out_dir}")


if __name__ == "__main__":
    main()
