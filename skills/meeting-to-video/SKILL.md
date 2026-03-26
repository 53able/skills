---
name: meeting-to-video
description: "ミーティングのトランスクリプト（プレーンテキスト）から Remotion ストーリー型ビデオプロジェクトを生成する。npx remotion preview でローカルプレビューできる状態まで自動構築する。Use when: meeting transcript, meeting summary video, meeting recap video, ミーティング動画, 議事録動画。"
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

リポジトリ内の単一スキルだけ入れたい場合:

```bash
npx skills add https://github.com/53able/skills/tree/main/skills/meeting-to-video -g
```

## Remotion rules to load

Remotion コードを触る前に `remotion-best-practices` のガイドを参照する：

- `animations.md`、`timing.md`、`transitions.md`、`sequencing.md`
- `text-animations.md`、`parameters.md`、`calculate-metadata.md`
- `voiceover.md`（ボイスオーバー時のみ）

**どこから読むか（優先順）**

1. **`setup.sh` 完了後（通常）** — プロジェクト直下の `.agents/skills/remotion-best-practices/` に展開された `SKILL.md` および `rules/*.md` を `Read` する（`npx skills` の標準配置）。
2. **マーカーが無い／オフラインで setup した場合** — [remotion-dev/skills](https://github.com/remotion-dev/skills) のリポジトリ上の該当 `.md`、または [Remotion 公式ドキュメント](https://remotion.dev/docs) を参照する。

`setup.sh` が `remotion-best-practices` を未検出なら `npx skills add remotion-dev/skills --yes` を実行する。手動で先に入れておいてもよい（マーカーがあれば setup はスキップする）。

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

`scripts/resolve-skill-dir.sh` を source して `MEETING_TO_VIDEO_SKILL_DIR` を確定し、`setup.sh` を実行する。候補パスは [vercel-labs/skills](https://github.com/vercel-labs/skills) の Supported Agents に追従している。

```bash
_rs=""
for d in \
  "$HOME/.config/agents/skills/meeting-to-video" \
  "$HOME/.gemini/antigravity/skills/meeting-to-video" \
  "$HOME/.augment/skills/meeting-to-video" \
  "$HOME/.claude/skills/meeting-to-video" \
  "$HOME/.openclaw/skills/meeting-to-video" \
  "$HOME/.agents/skills/meeting-to-video" \
  "$HOME/.codebuddy/skills/meeting-to-video" \
  "$HOME/.codex/skills/meeting-to-video" \
  "$HOME/.commandcode/skills/meeting-to-video" \
  "$HOME/.continue/skills/meeting-to-video" \
  "$HOME/.snowflake/cortex/skills/meeting-to-video" \
  "$HOME/.config/crush/skills/meeting-to-video" \
  "$HOME/.cursor/skills/meeting-to-video" \
  "$HOME/.deepagents/agent/skills/meeting-to-video" \
  "$HOME/.factory/skills/meeting-to-video" \
  "$HOME/.gemini/skills/meeting-to-video" \
  "$HOME/.copilot/skills/meeting-to-video" \
  "$HOME/.config/goose/skills/meeting-to-video" \
  "$HOME/.junie/skills/meeting-to-video" \
  "$HOME/.iflow/skills/meeting-to-video" \
  "$HOME/.kilocode/skills/meeting-to-video" \
  "$HOME/.kiro/skills/meeting-to-video" \
  "$HOME/.kode/skills/meeting-to-video" \
  "$HOME/.mcpjam/skills/meeting-to-video" \
  "$HOME/.vibe/skills/meeting-to-video" \
  "$HOME/.mux/skills/meeting-to-video" \
  "$HOME/.config/opencode/skills/meeting-to-video" \
  "$HOME/.openhands/skills/meeting-to-video" \
  "$HOME/.pi/agent/skills/meeting-to-video" \
  "$HOME/.qoder/skills/meeting-to-video" \
  "$HOME/.qwen/skills/meeting-to-video" \
  "$HOME/.roo/skills/meeting-to-video" \
  "$HOME/.trae/skills/meeting-to-video" \
  "$HOME/.trae-cn/skills/meeting-to-video" \
  "$HOME/.codeium/windsurf/skills/meeting-to-video" \
  "$HOME/.zencoder/skills/meeting-to-video" \
  "$HOME/.neovate/skills/meeting-to-video" \
  "$HOME/.pochi/skills/meeting-to-video" \
  "$HOME/.adal/skills/meeting-to-video" \
  "$HOME/.windsurf/skills/meeting-to-video" \
  ".claude/skills/meeting-to-video" \
  ".agents/skills/meeting-to-video"; do
  if [[ -f "$d/scripts/resolve-skill-dir.sh" ]]; then
    # shellcheck source=/dev/null
    source "$d/scripts/resolve-skill-dir.sh"
    break
  fi
done

if [[ -z "${MEETING_TO_VIDEO_SKILL_DIR:-}" ]]; then
  echo "ERROR: meeting-to-video が見つかりません。npx skills add でインストールするか、次のようにクローン内の resolve を直接 source してから再実行してください。" >&2
  echo "  source /絶対パス/skills/meeting-to-video/scripts/resolve-skill-dir.sh" >&2
  exit 1
fi

bash "$MEETING_TO_VIDEO_SKILL_DIR/scripts/setup.sh" <output-dir>
```

`setup.sh` は `npm ci` のあと、`<output-dir>/.agents/skills/remotion-best-practices/SKILL.md` が無ければ `npx skills add remotion-dev/skills --yes` を実行する（ネットワーク必須）。

リポジトリをクローンしただけで上記ループがヒットしない場合は、`skills/meeting-to-video/scripts/resolve-skill-dir.sh` を絶対パスで `source` すればよい（スクリプト末尾の候補がそのクローンをスキルルートとして採用する）。

完了後、テンプレートの `content.json`（サンプルデータ）を Step 2 の JSON で**上書き**:

```
Write: <output-dir>/content.json ← Step 2 の JSON
```

### Step 3b: Remotion 公式スキル（通常は自動）

`setup.sh` 内で処理する。手動で入れ直したい場合のみ:

```bash
cd <output-dir> && npx skills add remotion-dev/skills --yes
```

### Step 4: ボイスオーバー（ユーザーが要求した場合のみ）

```bash
# Step 3 で source 済みなら MEETING_TO_VIDEO_SKILL_DIR をそのまま使う
# 別セッションの場合は Step 3 と同じ for + source で再解決する

# ElevenLabs（デフォルト、引数なし）
bash "$MEETING_TO_VIDEO_SKILL_DIR/scripts/gen-audio.sh" <output-dir>

# OpenAI TTS
bash "$MEETING_TO_VIDEO_SKILL_DIR/scripts/gen-audio.sh" <output-dir> --provider openai
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
| `npm ci` 失敗 | `node --version` で v18+ を確認。`package-lock.json` が壊れていないか確認。どうしても通らない場合は `cd <output-dir> && rm -rf node_modules && npm install` で代替（ロックとズレる可能性あり） |
| `npx skills add remotion-dev/skills` 失敗（setup 内） | ネットワーク・`npx skills` を確認。手動で `cd <output-dir> && npx skills add remotion-dev/skills --yes` を再試行。どうしても不可なら [Remotion 公式ドキュメント](https://remotion.dev/docs) または [remotion-dev/skills](https://github.com/remotion-dev/skills) を参照して続行 |
| プレビュー起動失敗 | `npx remotion preview --port 3001` でポート変更 |
| TTS API 失敗 | ボイスオーバーなしで続行（音声はオプション） |
