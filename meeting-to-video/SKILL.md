---
name: meeting-to-video
description: ミーティングのトランスクリプト（プレーンテキスト）から Remotion ストーリー型ビデオプロジェクトを生成する。`npx remotion preview` でローカルプレビューできる状態まで自動構築する。Use when: meeting transcript, meeting summary video, meeting recap video, ミーティング動画, 議事録動画。
---

# Meeting to Video

## When to use

ミーティングのトランスクリプト（テキスト）を受け取り、2分間のエクスプレイナービデオにしたいとき。

## Prerequisites

- Node.js v18+、npm v9+
- `npx skills` CLI（任意。Cursor / Claude Code 環境で自動インストールを試みる）
- ボイスオーバーを使う場合: `ELEVENLABS_API_KEY`（デフォルト）または `OPENAI_API_KEY`

## インストール（初回のみ）

[npx skills](https://github.com/vercel-labs/skills) で Claude Code / Cursor / Codex / Gemini CLI など 40+ エージェントへ一括インストール:

```bash
# グローバルインストール（全検出済みエージェントへ）
npx skills add 53able/skills --skill meeting-to-video -g

# 特定エージェントのみ
npx skills add 53able/skills --skill meeting-to-video -g -a claude-code
npx skills add 53able/skills --skill meeting-to-video -g -a cursor
npx skills add 53able/skills --skill meeting-to-video -g -a codex -a gemini-cli

# 確認のみ（インストールしない）
npx skills add 53able/skills --list
```

スキルはシンボリックリンクで各エージェントに展開されるため、リポジトリを更新すれば全プラットフォームに即時反映される。

`npx skills` が使えない環境では `meeting-to-video/install.sh` でフォールバックインストールができる。

## Remotion rules to load

Remotionコードを触る前に必ず `remotion-best-practices` スキルの以下を参照：
- `animations.md`、`timing.md`、`transitions.md`、`sequencing.md`
- `text-animations.md`、`parameters.md`、`calculate-metadata.md`
- `voiceover.md`（ボイスオーバー時のみ）

## Workflow

### Step 1: トランスクリプト受け取り

プレーンテキストをそのまま、またはファイルパスを `Read` ツールで読み込む。

### Step 2: VideoProps JSON 生成

`prompts/extract.md` のプロンプトに従いトランスクリプトを分析し、`VideoPropsSchema` 準拠の JSON を生成する。生成後にバリデーション:

```
VideoPropsSchema.parse(generated_json)
```

失敗時はエラー内容を確認して JSON を修正し再試行する。

### Step 3: プロジェクトセットアップ

スキルのインストール先を自動解決してから実行する（npx skills でインストールした全エージェントに対応）:

```bash
_skill_dir=$(for d in \
  "$HOME/.claude/skills/meeting-to-video" \
  "$HOME/.cursor/skills/meeting-to-video" \
  "$HOME/.codex/skills/meeting-to-video" \
  "$HOME/.gemini/skills/meeting-to-video" \
  "$HOME/.codeium/windsurf/skills/meeting-to-video" \
  "$HOME/.copilot/skills/meeting-to-video" \
  "$HOME/.config/opencode/skills/meeting-to-video" \
  "$HOME/.config/agents/skills/meeting-to-video" \
  "$HOME/.agents/skills/meeting-to-video"; do
  [ -d "$d/scripts" ] && echo "$d" && break
done)

bash "$_skill_dir/scripts/setup.sh" <output-dir>
```

完了後、テンプレートの `content.json`（サンプルデータ）を Step 2 の JSON で**上書き**:

```
Write: <output-dir>/content.json ← Step 2 の JSON
```

### Step 4: ボイスオーバー（ユーザーが要求した場合のみ）

```bash
# Step 3 の _skill_dir 変数を使い回す（同一セッションの場合）
# 別セッションの場合は上記と同じ for ループで再解決する

# ElevenLabs（デフォルト、引数なし）
bash "$_skill_dir/scripts/gen-audio.sh" <output-dir>

# OpenAI TTS
bash "$_skill_dir/scripts/gen-audio.sh" <output-dir> --provider openai
```

### Step 5: プレビュー起動

```bash
cd <output-dir> && npx remotion preview
```

ブラウザで http://localhost:3000 を開くよう案内する。

## Error recovery

| エラー | 対応 |
|---|---|
| Zodバリデーション失敗 | エラー詳細を確認してJSONを修正、再バリデーション |
| npm install 失敗 | `node --version` で v18+ を確認 |
| `npx skills add` 失敗 | リトライ後も失敗する場合はスキップして続行 |
| プレビュー起動失敗 | `npx remotion preview --port 3001` でポート変更 |
| TTS API 失敗 | ボイスオーバーなしで続行（音声はオプション） |
