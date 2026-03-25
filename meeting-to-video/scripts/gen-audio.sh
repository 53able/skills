#!/bin/bash
# Usage:
#   bash gen-audio.sh <output-dir>                    # ElevenLabs (default)
#   bash gen-audio.sh <output-dir> --provider openai  # OpenAI TTS
#
# Environment variables:
#   ELEVENLABS_API_KEY  - required when --provider elevenlabs (default)
#   OPENAI_API_KEY      - required when --provider openai

set -e

OUTPUT_DIR="${1:?Usage: bash gen-audio.sh <output-dir> [--provider elevenlabs|openai]}"
PROVIDER="elevenlabs"

shift
while [[ $# -gt 0 ]]; do
  case "$1" in
    --provider) PROVIDER="$2"; shift 2 ;;
    *) shift ;;
  esac
done

CONTENT_JSON="$OUTPUT_DIR/content.json"
AUDIO_DIR="$OUTPUT_DIR/public/audio"

if [[ ! -f "$CONTENT_JSON" ]]; then
  echo "ERROR: $CONTENT_JSON not found. Run setup.sh and write content.json first." >&2
  exit 1
fi

if [[ "$PROVIDER" == "elevenlabs" ]]; then
  : "${ELEVENLABS_API_KEY:?ERROR: ELEVENLABS_API_KEY is not set}"
elif [[ "$PROVIDER" == "openai" ]]; then
  : "${OPENAI_API_KEY:?ERROR: OPENAI_API_KEY is not set}"
else
  echo "ERROR: Unknown provider: $PROVIDER (use elevenlabs or openai)" >&2
  exit 1
fi

mkdir -p "$AUDIO_DIR"

# narrationが存在するフェーズのみ処理。JSON.stringifyでエスケープし安全に埋め込む
CONTENT_JSON="$CONTENT_JSON" \
AUDIO_DIR="$AUDIO_DIR" \
PROVIDER="$PROVIDER" \
ELEVENLABS_API_KEY="${ELEVENLABS_API_KEY:-}" \
OPENAI_API_KEY="${OPENAI_API_KEY:-}" \
node -e "
const fs = require('fs');
const path = require('path');
const https = require('https');

const content = JSON.parse(fs.readFileSync(process.env.CONTENT_JSON, 'utf-8'));
const provider = process.env.PROVIDER;
const audioDir = process.env.AUDIO_DIR;

/** HTTPSでPOSTしてファイルに保存する。4xx/5xxはエラーとして reject する */
const postToFile = (targetUrl, headers, body, outputPath) =>
  new Promise((resolve, reject) => {
    const parsed = new URL(targetUrl);
    const req = https.request(
      { hostname: parsed.hostname, path: parsed.pathname + (parsed.search || ''), method: 'POST', headers },
      (res) => {
        const chunks = [];
        res.on('data', (c) => chunks.push(c));
        res.on('end', () => {
          if (res.statusCode < 200 || res.statusCode >= 300) {
            reject(new Error(\`HTTP \${res.statusCode}: \${Buffer.concat(chunks).toString()}\`));
            return;
          }
          fs.writeFileSync(outputPath, Buffer.concat(chunks));
          resolve();
        });
      }
    );
    req.on('error', reject);
    req.write(body);
    req.end();
  });

(async () => {
  for (const [i, phase] of content.phases.entries()) {
    if (!phase.narration) continue;
    const index = i + 1;
    const outputFile = path.join(audioDir, \`phase-\${index}.mp3\`);
    console.log(\`→ Generating audio for phase \${index}...\`);

    if (provider === 'elevenlabs') {
      const body = JSON.stringify({ text: phase.narration, model_id: 'eleven_multilingual_v2' });
      await postToFile(
        'https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM',
        { 'xi-api-key': process.env.ELEVENLABS_API_KEY, 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) },
        body,
        outputFile
      );
    } else if (provider === 'openai') {
      const body = JSON.stringify({ model: 'tts-1', voice: 'alloy', input: phase.narration });
      await postToFile(
        'https://api.openai.com/v1/audio/speech',
        { 'Authorization': \`Bearer \${process.env.OPENAI_API_KEY}\`, 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) },
        body,
        outputFile
      );
    }
    console.log(\`  ✓ \${outputFile}\`);
  }
  // content.json の withVoiceover を true に更新（次回プレビューで音声が有効になる）
  content.withVoiceover = true;
  fs.writeFileSync(process.env.CONTENT_JSON, JSON.stringify(content, null, 2));
  console.log('  ✓ content.json updated: withVoiceover = true');

  console.log('✓ Audio generation complete');
})().catch((e) => {
  console.error('ERROR:', e.message);
  process.exit(1);
});
"
