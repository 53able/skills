#!/usr/bin/env bash
# 使い方: bash scripts/check-env.sh
# Pake のビルドに必要な前提環境を検証する。
# 終了コード 0 = 全項目 OK、終了コード 1 = 前提条件が不足。

set -euo pipefail

ERRORS=()

# Node.js >= 18 の確認
if ! command -v node &>/dev/null; then
  ERRORS+=("node: 見つかりません — Node.js >= 18 をインストールしてください (https://nodejs.org)")
else
  NODE_VERSION=$(node -e "process.stdout.write(process.versions.node)")
  MAJOR=${NODE_VERSION%%.*}
  if (( MAJOR < 18 )); then
    ERRORS+=("node: バージョン ${NODE_VERSION} は古すぎます — >= 18 が必要です")
  else
    echo "OK node ${NODE_VERSION}"
  fi
fi

# npx の確認（npm >= 5.2 に同梱）
if ! command -v npx &>/dev/null; then
  ERRORS+=("npx: 見つかりません — npm を >= 5.2 にアップデートしてください")
else
  echo "OK npx $(npx --version)"
fi

# Rust の確認（初回ビルド時に pake-cli が自動インストールするため警告のみ）
if ! command -v rustc &>/dev/null; then
  echo "WARN rustc: 見つかりません — 初回ビルド時に Pake が自動インストールを試みます（追加で約 5〜10 分かかります）"
else
  echo "OK rustc $(rustc --version)"
fi

# ~/Downloads ディレクトリの確認
if [[ ! -d "$HOME/Downloads" ]]; then
  ERRORS+=("~/Downloads: ディレクトリが存在しません — mkdir ~/Downloads で作成してください")
else
  echo "OK ~/Downloads"
fi

if (( ${#ERRORS[@]} > 0 )); then
  echo "" >&2
  echo "環境エラー:" >&2
  for e in "${ERRORS[@]}"; do
    echo "  - ${e}" >&2
  done
  exit 1
fi

echo ""
echo "全ての前提条件を満たしています。ビルドを開始できます。"
