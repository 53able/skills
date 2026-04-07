#!/usr/bin/env bash
# Usage: bash scripts/check-granularity.sh
# 現在の差分（ステージ済み＋未ステージ）を分析し、
# コミット粒度の観点から概要レポートを出力する。

set -euo pipefail

WARN_FILE_THRESHOLD=10
WARN_LINE_THRESHOLD=300

staged_files=$(git diff --cached --name-only 2>/dev/null | wc -l | tr -d ' ')
unstaged_files=$(git diff --name-only 2>/dev/null | wc -l | tr -d ' ')
staged_lines=$(git diff --cached --stat 2>/dev/null | tail -1)

echo "=== コミット粒度チェック ==="
echo ""
echo "[ステージ済み]"
echo "  変更ファイル数 : ${staged_files}"
echo "  差分サマリー   : ${staged_lines:-（変更なし）}"
echo ""
echo "[未ステージ]"
echo "  変更ファイル数 : ${unstaged_files}"
echo ""

# 変更の目的が複数混在していないかヒューリスティックに確認
staged_types=$(git diff --cached --name-only 2>/dev/null \
  | sed 's|.*\.||' \
  | sort -u \
  | tr '\n' ' ')
echo "[ステージ済みのファイル拡張子] ${staged_types:-（なし）}"
echo ""

# 警告: ファイル数が多い場合
if [ "${staged_files}" -gt "${WARN_FILE_THRESHOLD}" ]; then
  echo "WARNING: ステージ済みファイルが ${staged_files} 件と多め。" >&2
  echo "         複数の論理グループが混在していないか確認してください。" >&2
fi

# 警告: セマンティックギャップの疑い（削除ファイルと新規ファイルが別れていないか）
deleted=$(git diff --cached --diff-filter=D --name-only 2>/dev/null | wc -l | tr -d ' ')
added=$(git diff --cached --diff-filter=A --name-only 2>/dev/null | wc -l | tr -d ' ')
if [ "${deleted}" -gt 0 ] && [ "${added}" -gt 0 ]; then
  echo "INFO: 削除ファイル ${deleted} 件 / 追加ファイル ${added} 件 が混在しています。"
  echo "      関数の移動が分割されていないか確認してください。"
fi

echo ""
echo "=== チェック完了 ==="
