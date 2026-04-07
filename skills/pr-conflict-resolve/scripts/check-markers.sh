#!/usr/bin/env zsh
# 使い方: ./scripts/check-markers.sh
# ステージ済みファイルにgitコンフリクトマーカーが残っていないかをスキャンする。
# クリーンなら exit 0、マーカーが見つかれば対象ファイルを stderr に出力して exit 1。

set -euo pipefail

readonly MARKERS=('<<<<<<<' '=======' '>>>>>>>')

staged_files=$(git diff --cached --name-only --diff-filter=ACM)

if [[ -z "$staged_files" ]]; then
  echo "ステージ済みファイルがありません。" >&2
  exit 0
fi

found=0
while IFS= read -r file; do
  for marker in "${MARKERS[@]}"; do
    if grep -qF "$marker" "$file" 2>/dev/null; then
      echo "コンフリクトマーカー検出: $file （'$marker' が残存）" >&2
      found=1
      break
    fi
  done
done <<< "$staged_files"

if [[ "$found" -eq 1 ]]; then
  echo "コミットする前にすべてのコンフリクトマーカーを解消してください。" >&2
  exit 1
fi

echo "OK: ステージ済みファイルにコンフリクトマーカーは検出されませんでした。"
exit 0
