# AGENTS.md

このリポジトリは [vercel-labs/skills](https://github.com/vercel-labs/skills)（`npx skills`）向けのエージェントスキル集である。

## レイアウト

- 各スキルは `skills/<skill-name>/` に置く。`SKILL.md` はそのディレクトリ直下に置き、[Agent Skills の慣習](https://github.com/vercel-labs/skills)に合わせる。
- `npx skills add <このリポジトリ>` は `skills/` を優先して走査するため、ルート直下にスキルフォルダを置かない。

## インストール（利用者向け）

```bash
npx skills add 53able/skills
npx skills add 53able/skills --skill meeting-to-video -g
```

単一スキルだけ（サブパス指定）:

```bash
npx skills add https://github.com/53able/skills/tree/main/skills/meeting-to-video -g
```

## meeting-to-video のメモ

- 手動の `install.sh` は置かない。インストールは `npx skills` のみ。
- `setup.py` は `npm ci` のあと、プロジェクトに `remotion-best-practices` が無ければ `npx skills add remotion-dev/skills --yes` を実行する（`.agents/skills/remotion-best-practices/SKILL.md` をマーカーにする）。
- テンプレの `package.json` の `overrides.loader-utils` は、Remotion の bundler が advisory 済みの `loader-utils` を引かなくなったら削除を検討する。
- スキルルート解決の単一ソースは `skills/meeting-to-video/scripts/resolve_skill_dir.py`。Supported Agents のグローバルパス変更時はここと `SKILL.md` の Step 3 ループを同期する。

## スキル記述規則

- スキルフォルダに同梱されているファイル（スクリプト・テンプレート・リファレンスなど）を prose で言及する場合は、念のために **`スキル同梱の`** を前置きする。
  - 例: `スキル同梱の \`scripts/check_granularity.py\` を実行する`
  - コードブロック内のコマンドには不要。prose の説明文でのみ付ける。

## 変更時のチェック

- `README.md` のパス例がリポジトリ構造と一致しているか。
- `meeting-to-video` のワークフローで `setup.py` / `gen_audio.py` が `MEETING_TO_VIDEO_SKILL_DIR` または `resolve_skill_dir.py` 経由で動くか。
