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
- `setup.sh` は `npm ci` のみ（`package-lock.json` 固定）。Remotion 公式スキルは `SKILL.md` Step 3b で任意実行。
- スキルルート解決の単一ソースは `skills/meeting-to-video/scripts/resolve-skill-dir.sh`。Supported Agents のグローバルパス変更時はここと `SKILL.md` の Step 3 ループを同期する。

## 変更時のチェック

- `README.md` のパス例がリポジトリ構造と一致しているか。
- `meeting-to-video` のワークフローで `setup.sh` / `gen-audio.sh` が `MEETING_TO_VIDEO_SKILL_DIR` または `resolve-skill-dir.sh` 経由で動くか。
