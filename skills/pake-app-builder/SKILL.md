---
name: pake-app-builder
description: Pake（Tauri ベースの軽量ラッパー）を使ってウェブ URL を macOS・Windows・Linux 向けのネイティブデスクトップアプリに変換する。任意のウェブページやウェブアプリを小さなバイナリのスタンドアロンアプリにパッケージしたいときに使う。npx 経由で常に最新版を利用する。Electron 固有の API・サーバーサイド処理・Node.js 統合・WebView ラッパーを超えた複雑なネイティブシステムコールが必要なアプリには使わない。
---

# Pake アプリビルダー

任意のウェブ URL を [Pake](https://github.com/tw93/Pake)（Rust + Tauri v2）を使ってネイティブデスクトップアプリ（約 5 MB）に変換する。
出力先は `~/Downloads`。

---

## 手順

**ステップ 1: 入力情報の収集**

ユーザーのリクエストから以下のパラメータを収集する:

| パラメータ          | 必須 | 説明                                        | デフォルト       |
|---------------------|------|---------------------------------------------|-----------------|
| `url`               | 必須 | 変換対象のウェブ URL                         | —               |
| `name`              | 必須 | アプリ名（スペースなし推奨）                 | —               |
| `width`             | 任意 | ウィンドウ幅（px）                          | `1200`          |
| `height`            | 任意 | ウィンドウ高さ（px）                        | `780`           |
| `icon`              | 任意 | アイコンのパスまたは URL                    | サイトから自動取得 |
| `hide-title-bar`    | 任意 | 没入型タイトルバー（macOS のみ）            | `false`         |
| `show-system-tray`  | 任意 | システムトレイアイコンを有効化              | `false`         |
| `fullscreen`        | 任意 | フルスクリーンで起動                        | `false`         |
| `debug`             | 任意 | ビルドしたアプリで DevTools を有効化        | `false`         |
| `targets`           | 任意 | Linux 出力形式（`deb`, `appimage`）         | OS デフォルト   |

`name` が指定されていない場合は、URL のホスト名から導出する（例: `github.com` → `GitHub`）。

**ステップ 2: 環境チェック**

環境確認スクリプトを実行する:

```bash
bash ~/.agents/skills/pake-app-builder/scripts/check-env.sh
```

- スクリプトが終了コード `1` で終了した場合は、エラー内容をユーザーに報告して処理を停止する。
- `rustc` が見つからない場合は、初回ビルド時に Rust が自動インストールされるため追加で 5〜10 分かかる旨をユーザーに伝える。

**ステップ 3: アプリのビルド**

`~/Downloads` に移動してから `npx pake-cli@latest` を実行することで、成果物が確実に `~/Downloads` へ出力される。

コマンドを構築する:

```bash
cd ~/Downloads && npx pake-cli@latest "<url>" --name "<name>" [オプション]
```

**最小構成の例:**
```bash
cd ~/Downloads && npx pake-cli@latest "https://github.com" --name GitHub
```

**オプション全指定の例:**
```bash
cd ~/Downloads && npx pake-cli@latest "https://app.example.com" \
  --name MyApp \
  --width 1400 \
  --height 900 \
  --icon https://app.example.com/favicon.ico \
  --hide-title-bar \
  --show-system-tray
```

ユーザーが明示的に要求したフラグのみ付与する。
非標準のオプションが要求された場合は `references/cli-options.md` を参照して正確なフラグを確認する。

**ステップ 4: 出力の確認**

ビルド完了後、成果物の存在を確認する:

```bash
ls -lh ~/Downloads/*.dmg ~/Downloads/*.exe ~/Downloads/*.deb ~/Downloads/*.AppImage 2>/dev/null | head -20
```

ファイル名・サイズ・フルパスをユーザーに報告する。

---

## デシジョンツリー

```
URL が提供されているか?
├── いいえ → URL を尋ねてから進める
└── はい   → アプリ名が提供されているか?
              ├── いいえ → ホスト名から導出する
              └── はい   → ステップ 2（環境チェック）を実行
                            ├── FAIL → エラーを報告して停止
                            └── OK   → ステップ 3（ビルド）を実行
                                        ├── ビルドエラー → エラー対処を参照
                                        └── 成功         → ステップ 4（出力確認）を実行
```

---

## エラー対処

| エラー                                              | 対処方法                                                                                                        |
|-----------------------------------------------------|-----------------------------------------------------------------------------------------------------------------|
| `rustc` が見つからない / Rust インストール失敗      | `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \| sh -s -- -y` を実行してリトライ                  |
| `npx` が見つからない / Node.js バージョンが低い    | https://nodejs.org から Node.js >= 18 をインストールしてリトライ                                                |
| `error[E...]` Rust コンパイルエラー                 | `--debug` フラグを外して再実行。OS の Tauri 前提条件を確認する                                                  |
| アイコン取得失敗（404 / 非対応フォーマット）        | `--icon` フラグを省略する — Pake がサイトの favicon を自動取得する                                              |
| `~/Downloads` に出力ファイルが見つからない          | カレントディレクトリを確認。`npx pake-cli` の前に `cd ~/Downloads` が実行されているか確認する                    |
| macOS: 「開発元を確認できないため開けません」       | `xattr -cr ~/Downloads/<AppName>.app` を実行してから再度開く                                                    |
| Windows/macOS で `--targets` が無視される           | `--targets` は Linux 専用フラグ。他の OS では省略する                                                           |
