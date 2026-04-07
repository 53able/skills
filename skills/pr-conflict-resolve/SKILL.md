---
name: pr-conflict-resolve
description: ローカルCLI（git / gh）を使ってGitHub PRのコンフリクトを解消する。merge vs rebase の戦略選択、コンフリクトマーカーの解消、安全な復旧手順、プッシュ後のPR確認チェックリストまでをガイドする。PRにコンフリクトが発生したとき、featureブランチをmainと同期するとき、コンフリクト解消後の復旧が必要なときに使う。コンフリクトを伴わないコードレビュー、PR以外の一般的なgit操作、リポジトリの初期セットアップには使わない。
---

# PR コンフリクト解消

## 手順

**Step 1: 安全確認**
1. 作業を開始する前に、作業ディレクトリがクリーンであることを確認する:
   ```zsh
   git status
   ```
   出力に "nothing to commit, working tree clean" が表示されていることを確認する。未コミットの変更がある場合は先にスタッシュまたはコミットする。
2. 現在の状態を保存するバックアップブランチを作成する:
   ```zsh
   git branch backup-feature-branch
   ```
3. アップストリームの最新情報を取得する:
   ```zsh
   git fetch origin
   ```

**Step 2: 戦略選択**
1. 作業前にチームの同期戦略を確認する。merge と rebase のトレードオフ比較マトリクスは `references/strategy-guide.md` を読む。
2. 選択した戦略を実行する:
   - **Merge（デフォルト — 共有ブランチに安全）:**
     ```zsh
     git merge origin/main
     ```
   - **Rebase（履歴を一直線にする — 非共有ブランチ専用）:**
     ```zsh
     git rebase origin/main
     ```

**Step 3: コンフリクト解消**
1. コンフリクトしているファイルをすべて確認する:
   ```zsh
   git status
   ```
   "Unmerged paths" に列挙されたファイルが解消対象。
2. 各コンフリクトファイルを開き、以下のマーカーを探す:
   - `<<<<<<< HEAD` — 現在のブランチの変更
   - `=======` — 境界線
   - `>>>>>>> origin/main` — 取り込もうとしているブランチの変更
3. 双方の意図を汲み取り、最終的に正しいコードへ書き換え、3種のマーカーをすべて削除する。
4. ローカルでテストまたはビルドを実行し、ロジックが壊れていないことを確認する。
5. 解消済みの各ファイルをステージする:
   ```zsh
   git add <解決したファイル名>
   ```
6. コミット前に `scripts/check-markers.sh` を実行してマーカーの残留がないことを検証する。

**Step 4: コミットとプッシュ**
1. Merge 戦略の場合 — マージコミットを作成する:
   ```zsh
   git commit
   ```
2. Rebase 戦略の場合 — リベースを再開する:
   ```zsh
   git rebase --continue
   ```
3. PRを更新するためにプッシュする:
   - Merge: `git push origin <ブランチ名>`
   - Rebase: `git push --force-with-lease origin <ブランチ名>`
     （`--force-with-lease` は自分が把握していないリモートの更新があった場合に上書きをブロックする。bare `--force` は使わない。）

**Step 5: PR確認**
1. ブラウザでPRを開く:
   ```zsh
   gh pr view --web
   ```
2. UI上の "Resolve conflicts" 警告が消え、"Merge pull request" が有効になっていることを確認する。
3. "Files changed" タブを開き、意図しない空白や書式の差分が混入していないかを確認する。
4. ステータスチェック（CI/CD・lint）がすべてパスしていることを確認する:
   ```zsh
   gh pr checks
   ```
5. CIが一時的なエラーで失敗した場合は、GitHub UI の再実行ボタンから手動再トリガーする。
6. 非自明なロジック変更を伴う解消をした場合は、Conversation タブに調整内容のコメントを残す。
7. 既存のインラインレビューコメントと、今回の解消内容が矛盾していないかを確認する。
8. CODEOWNERS の承認が必要なリポジトリ設定になっていないかを確認し、必要なら承認を依頼する。
9. 以前に "Changes requested" が出されていた場合、解消済みになっているかを確認する。
10. Reviewers パネルの "Re-request review" アイコンから明示的に再レビュー依頼を実行する。

## 最小検証（30秒）
解消完了後、必ず以下の3コマンドを実行する:
```zsh
# 未解決ファイル・未ステージの変更がないか確認
git status

# 直近のコミットが正しく積まれているか確認
git log --oneline -n 3

# CLIからCIチェック状況を確認
gh pr checks
```

## エラーハンドリング
- `scripts/check-markers.sh` がマーカー残留を報告した場合は、対象ファイルを再度開いてマーカーを削除してからコミットする。
- マージまたはリベースを完全に中断したい場合:
  ```zsh
  git merge --abort
  # または
  git rebase --abort
  ```
  どちらのコマンドも操作開始前の状態に安全に戻す。
- ブランチの状態をバックアップに完全リセットしたい場合:
  ```zsh
  git reset --hard backup-feature-branch
  ```
- 誤ったコミットをすでにプッシュしてしまった場合は `git reflog` で履歴を確認し、安全な時点に戻す:
  ```zsh
  git reflog
  git reset --hard HEAD@{n}
  ```
- `.orig` などの一時ファイルを誤ってステージした場合は `git restore --staged <ファイル名>` でアンステージし、`.gitignore` に追加する。
- 典型的なコンフリクトパターンの詳細と復旧手順は `references/conflict-patterns.md` を読む。
