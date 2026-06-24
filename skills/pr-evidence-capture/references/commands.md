# 具体コマンドと PR コメントテンプレート

SKILL.md のワークフローで使うコマンドの詳細。OWNER/REPO は通常カレントリポジトリでよい（`gh repo view --json nameWithOwner` で確認）。

## Step 1: PR 情報と差分の取得

```bash
# 現在のブランチに紐づく PR 番号・本文・head を取得
gh pr view --json number,title,body,headRefName,headRefOid

# 差分を確認してテスト計画の観点を洗い出す
gh pr diff <PR番号>
```

## Step 4: gh image でアップロード

`gh image <image-path>...` は画像をアップロードし、Markdown 画像参照を標準出力へ印字する。複数指定可。

```bash
# 単一
gh image ./tmp/case-a.png

# 複数（出力された Markdown 参照をコメントへ転記する）
gh image ./tmp/case-a.png ./tmp/case-c.png

# リポジトリを明示する場合
gh image --repo OWNER/REPO ./tmp/case-a.png
```

トークン関連:

```bash
gh image check-token        # 有効性確認（ユーザー名が出る）
gh image extract-token      # ブラウザからセッショントークンを取り出す
# 共有マシンでは GH_SESSION_TOKEN 環境変数を使う（--token はプロセス一覧に見える）
```

出力例（この Markdown をそのままコメント本文へ埋め込む）:

```markdown
![case-a](https://github.com/user-attachments/assets/xxxxxxxx-....)
```

## Step 5: gh pr comment で投稿

本文は `--body-file -` に HEREDOC で渡す。`-b`/`-f` の直接渡しは画像リンクや表が崩れやすい。

```bash
gh pr comment <PR番号> --body-file - <<'EOF'
## UI エビデンス

### Case A: 確認モーダル

![case-a](https://github.com/user-attachments/assets/...)

### Case C: モーダルをキャンセルした後

![case-c](https://github.com/user-attachments/assets/...)

## E2E テスト計画

### 対象範囲

このPRでは処理開始フローを変更する。確認が必要な対象項目がある場合は、開始前に確認モーダルを表示する。

### テストケース

1. 対象項目がある場合、確認モーダルが表示される
2. モーダルで確認すると、処理が開始される
3. モーダルをキャンセルすると、開始前ステータスのままになる
4. 対象項目が0件の場合、モーダルなしで処理が開始される

## E2E テスト結果

| ケース | 結果 | メモ |
|---|---:|---|
| Case A | Pass | 対象項目がモーダルに表示された |
| Case B | Pass | 確認後、対象リソースが実行中ステータスへ遷移した |
| Case C | Pass | キャンセル後、開始前ステータスのままだった |
| Case D | Pass | 対象0件の場合、モーダルなしで処理が開始された |

## 検証データへの副作用

| ケース | 検証後ステータス |
|---|---|
| Case B | 実行中 |
| Case D | 実行中 |
| Case A / Case C | 開始前 |

実行中になったデータは再検証に使い回さず、別の検証用データを用意すること。
EOF
```

既存コメントを最新の確認結果へ差し替える場合は、対象コメント ID を指定して編集する。

```bash
# PR のコメント一覧から ID を確認
gh api repos/OWNER/REPO/issues/<PR番号>/comments --jq '.[] | {id, body: .body[0:40]}'

# 既存コメントを更新
gh api --method PATCH repos/OWNER/REPO/issues/comments/<COMMENT_ID> --field body=@-  <<'EOF'
（更新後の本文）
EOF
```

## 注意

- GitHub コメントでは絵文字を使わない。
- 表・画像リンク・コードブロックを含む本文は必ず HEREDOC（`<<'EOF'`）で渡す。変数展開を避けるためクォート付きデリミタを使う。
