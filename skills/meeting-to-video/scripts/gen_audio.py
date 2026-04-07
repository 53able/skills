#!/usr/bin/env python3
# Usage:
#   python gen_audio.py <output-dir>                    # ElevenLabs (default)
#   python gen_audio.py <output-dir> --provider openai  # OpenAI TTS
#
# Environment variables:
#   ELEVENLABS_API_KEY  - required when --provider elevenlabs (default)
#   OPENAI_API_KEY      - required when --provider openai

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ELEVENLABS_URL = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"
OPENAI_URL = "https://api.openai.com/v1/audio/speech"


def post_to_file(url: str, headers: dict, body: bytes, output_path: Path) -> None:
    """HTTPS POST してレスポンスボディをファイルに書き込む。4xx/5xx は RuntimeError を送出する。"""
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            output_path.write_bytes(resp.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode()}") from e


def generate_elevenlabs(api_key: str, narration: str, output_path: Path) -> None:
    """ElevenLabs TTS API で音声を生成する。"""
    body = json.dumps(
        {"text": narration, "model_id": "eleven_multilingual_v2"}
    ).encode()
    post_to_file(
        ELEVENLABS_URL,
        {
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
        },
        body,
        output_path,
    )


def generate_openai(api_key: str, narration: str, output_path: Path) -> None:
    """OpenAI TTS API で音声を生成する。"""
    body = json.dumps(
        {"model": "tts-1", "voice": "alloy", "input": narration}
    ).encode()
    post_to_file(
        OPENAI_URL,
        {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
        },
        body,
        output_path,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="content.json の各フェーズのナレーションから音声ファイルを生成する"
    )
    parser.add_argument("output_dir", help="セットアップ済みの出力ディレクトリ")
    parser.add_argument(
        "--provider",
        choices=["elevenlabs", "openai"],
        default="elevenlabs",
        help="TTS プロバイダー (default: elevenlabs)",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    content_json_path = output_dir / "content.json"
    audio_dir = output_dir / "public" / "audio"

    if not content_json_path.exists():
        sys.exit(
            f"ERROR: {content_json_path} not found. "
            "Run setup.py and write content.json first."
        )

    if args.provider == "elevenlabs":
        api_key = os.environ.get("ELEVENLABS_API_KEY", "")
        if not api_key:
            sys.exit("ERROR: ELEVENLABS_API_KEY is not set")
    else:
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            sys.exit("ERROR: OPENAI_API_KEY is not set")

    audio_dir.mkdir(parents=True, exist_ok=True)
    content = json.loads(content_json_path.read_text(encoding="utf-8"))

    for i, phase in enumerate(content.get("phases", [])):
        if not phase.get("narration"):
            continue
        index = i + 1
        output_file = audio_dir / f"phase-{index}.mp3"
        print(f"→ Generating audio for phase {index}...")

        try:
            if args.provider == "elevenlabs":
                generate_elevenlabs(api_key, phase["narration"], output_file)
            else:
                generate_openai(api_key, phase["narration"], output_file)
        except RuntimeError as e:
            sys.exit(f"ERROR: {e}")

        print(f"  ✓ {output_file}")

    # content.json の withVoiceover を true に更新（次回プレビューで音声が有効になる）
    content["withVoiceover"] = True
    content_json_path.write_text(
        json.dumps(content, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("  ✓ content.json updated: withVoiceover = true")
    print("✓ Audio generation complete")


if __name__ == "__main__":
    main()
