# Pi CLI リファレンス

ソース: https://github.com/earendil-works/pi/blob/main/packages/coding-agent/README.md

## 呼び出し

```
pi [options] [@files...] [messages...]
```

## モード

| フラグ | モード |
|--------|--------|
| （デフォルト） | インタラクティブTUI |
| `-p`, `--print` | レスポンスを表示して終了 |
| `--mode json` | 全イベントをJSON行として出力 |
| `--mode rpc` | stdin/stdoutでRPC通信（JSONLフレーミング、`\n` のみで分割） |
| `--export <in> [out]` | セッションをHTMLにエクスポート |

## パッケージコマンド

```bash
pi install <source> [-l]         # インストール（npm:, git:, https://, ssh://）-l = プロジェクトローカル
pi remove <source> [-l]
pi uninstall <source> [-l]       # remove のエイリアス
pi update [source|self|pi]       # piおよびパッケージを更新
pi update --extensions           # パッケージのみ更新
pi update --self [--force]       # piバイナリのみ更新
pi list                          # インストール済みパッケージを一覧表示
pi config                        # リソースの有効化・無効化
```

## モデルオプション

| オプション | 説明 |
|-----------|------|
| `--provider <name>` | プロバイダ名（anthropic, openai, google など） |
| `--model <pattern>` | IDまたは `provider/id` または `name:thinking` 形式 |
| `--api-key <key>` | 環境変数を上書きするAPIキー |
| `--thinking <level>` | off, minimal, low, medium, high, xhigh |
| `--models <patterns>` | Ctrl+Pサイクル用のカンマ区切りパターン |
| `--list-models [search]` | 利用可能なモデルを一覧表示 |

## セッションオプション

| オプション | 説明 |
|-----------|------|
| `-c`, `--continue` | 直近のセッションを継続する |
| `-r`, `--resume` | セッションを選択して再開する |
| `--session <path|id>` | ファイルパスまたは部分UUIDでセッションを開く |
| `--fork <path|id>` | 既存セッションを新しいセッションファイルにフォークする |
| `--session-dir <dir>` | セッション保存ディレクトリを指定する |
| `--no-session` | エフェメラルモード（保存しない） |

## ツールオプション

| オプション | 説明 |
|-----------|------|
| `--tools <list>`, `-t` | ツール名の許可リスト（組み込み・Extension・カスタム） |
| `--no-builtin-tools`, `-nbt` | 組み込みツールを無効にする（Extensionツールは有効のまま） |
| `--no-tools`, `-nt` | 全ツールを無効にする |

組み込みツール: `read`, `bash`, `edit`, `write`, `grep`, `find`, `ls`

## リソースオプション

| オプション | 説明 |
|-----------|------|
| `-e`, `--extension <source>` | Extensionを読み込む（繰り返し指定可） |
| `--no-extensions` | 自動探索を無効にする |
| `--skill <path>` | スキルを読み込む（繰り返し指定可） |
| `--no-skills` | 自動探索を無効にする |
| `--prompt-template <path>` | プロンプトテンプレートを読み込む（繰り返し指定可） |
| `--no-prompt-templates` | 自動探索を無効にする |
| `--theme <path>` | テーマを読み込む（繰り返し指定可） |
| `--no-themes` | 自動探索を無効にする |
| `--no-context-files`, `-nc` | AGENTS.md / CLAUDE.md の読み込みを無効にする |

## その他のオプション

| オプション | 説明 |
|-----------|------|
| `--system-prompt <text>` | デフォルトのシステムプロンプトを置き換える |
| `--append-system-prompt <text>` | システムプロンプトに追記する |
| `--verbose` | 詳細な起動ログを強制表示する |
| `-h`, `--help` | ヘルプを表示する |
| `-v`, `--version` | バージョンを表示する |
| `--offline` | 起動時のネットワーク処理をすべて無効にする（バージョン確認・テレメトリ） |

## 環境変数

| 変数名 | 用途 |
|--------|------|
| `PI_CODING_AGENT_DIR` | `~/.pi/agent` 設定ディレクトリを上書き |
| `PI_CODING_AGENT_SESSION_DIR` | セッション保存ディレクトリを上書き |
| `PI_PACKAGE_DIR` | パッケージディレクトリを上書き |
| `PI_OFFLINE` | 起動時のネットワーク処理をすべて無効にする |
| `PI_SKIP_VERSION_CHECK` | バージョン確認のみスキップする |
| `PI_TELEMETRY` | `0`/`1` でインストールテレメトリを無効化/有効化 |
| `PI_CACHE_RETENTION` | `long` でプロンプトキャッシュを延長する |
| `VISUAL`, `EDITOR` | Ctrl+G で開く外部エディタ |
| `ANTHROPIC_API_KEY` など | プロバイダAPIキー |

## インタラクティブコマンド

| コマンド | 説明 |
|---------|------|
| `/login`, `/logout` | OAuth認証 |
| `/model` | モデルを切り替える |
| `/scoped-models` | Ctrl+Pサイクル対象モデルの有効化・無効化 |
| `/settings` | 思考レベル・テーマ・配信設定・トランスポートを変更 |
| `/resume` | 過去のセッションを選択する |
| `/new` | 新しいセッションを開始する |
| `/name <名前>` | 現在のセッションに名前をつける |
| `/session` | セッション情報（ファイル・ID・メッセージ数・トークン数・コスト）を表示 |
| `/tree` | セッションツリーをナビゲートする |
| `/fork` | 過去のユーザーメッセージから新しいセッションを作成する |
| `/clone` | アクティブブランチを新しいセッションに複製する |
| `/compact [指示]` | 手動でコンパクションする |
| `/copy` | 最後のアシスタントメッセージをクリップボードにコピーする |
| `/export [file]` | セッションをHTMLにエクスポートする |
| `/share` | プライベートGitHub gistとしてアップロードする |
| `/reload` | Extension・スキル・プロンプト・キーバインドを再読み込みする |
| `/hotkeys` | 全ショートカットを表示する |
| `/changelog` | バージョン履歴を表示する |
| `/quit` | 終了する |

## キーボードショートカット（デフォルト）

| キー | 動作 |
|-----|------|
| Ctrl+C | エディタをクリアする（×2で終了） |
| Escape | 中断・キャンセル（×2で /tree） |
| Ctrl+L | モデルセレクターを開く |
| Ctrl+P / Shift+Ctrl+P | スコープ付きモデルを順方向/逆方向にサイクル |
| Shift+Tab | 思考レベルをサイクル |
| Ctrl+O | ツール出力を折りたたむ/展開する |
| Ctrl+T | 思考ブロックを折りたたむ/展開する |
| Enter | ステアリングメッセージをキューに追加する（エージェント実行中） |
| Alt+Enter | フォローアップメッセージをキューに追加する |
| Alt+Up | キューのメッセージをエディタに戻す |

## ファイル引数

`@` をプレフィックスとして付けるとファイルの内容をメッセージに含める：

```bash
pi @prompt.md "これに答えて"
pi -p @screenshot.png "この画像には何が写っている？"
pi @code.ts @test.ts "これらをレビューして"
```
