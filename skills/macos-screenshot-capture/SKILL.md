---
name: macos-screenshot-capture
description: macOSのスクリーンショットを、screencaptureと補助CLIで取得する。画面全体、ウィンドウ指定、選択範囲、タイマー撮影、クリップボード保存に対応する。macOS上でエージェントが再現可能なパスへスクリーンショットを保存したい場合に使う。OCR、画像編集、動画収録、macOS以外のスクリーンショット取得には使わない。
---

# macOSスクリーンショット取得

## 手順

**Step 1: 撮影対象を決める**
1. 依頼内容から撮影モードを判定する: `full`、`window`、`window-id`、`app-window`、`selection`、`clipboard`、`timed`。
2. 依頼が曖昧な場合は、操作への影響が少ないモードを選ぶ。
   - 領域、範囲、部分、切り抜きが言及されている場合は `selection` を使う。
   - 特定のアプリやウィンドウが言及されている場合は `window` を使う。
   - 画面、デスクトップ、全体、全ディスプレイが言及されている場合は `full` を使う。
   - ファイル保存ではなく貼り付け用が求められている場合は `clipboard` を使う。
   - メニュー表示や画面準備の時間が必要な場合は `timed` を使う。
3. アプリ名が分かっている場合は `app-window` モードを使い、対象アプリの最大ウィンドウを自動検出して撮影する。
4. ウィンドウIDが既知の場合は `window-id` モードを使い、対話式クリックなしで対象ウィンドウを撮影する。
5. 特定ウィンドウを自動特定できない場合は、対話式の `window` モードを使い、macOS上で対象ウィンドウをクリックしてもらう。
6. `screencapture` の正確なフラグ確認が必要な場合だけ、`references/screencapture-options.md` を読む。

**Step 2: 出力パスを決める**
1. ユーザーが保存先を指定している場合は、そのパスへ保存する。
2. 保存先が未指定の場合は、`outputs/screenshots/screenshot-YYYYmmdd-HHMMSS.png` の形式で保存する。
3. 形式指定がない場合はPNGを使う。
4. ユーザーが明示的に上書きを求めていない限り、既存ファイルを上書きしない。

**Step 3: 撮影ヘルパーを実行する**
1. スキルディレクトリから `python3 scripts/capture_macos_screenshot.py --mode [mode]` を実行し、ファイル保存時は `--output [path]` を追加する。
2. `timed` モード、またはUI準備時間が必要な場合は `--delay [秒数]` を追加する。
3. 特定ディスプレイを指定する場合、または通常の全画面撮影が失敗する場合は `--display [番号]` を追加する。
4. アプリ名から対象ウィンドウを自動検出する場合は `--mode app-window --app [アプリ名]` を使う。タイトルで絞る場合は `--window-title [文字列]` を追加する。
5. 既知のウィンドウIDを撮影する場合は `--mode window-id --window-id [ID]` を使う。
6. 拡張子と異なる形式を明示する必要がある場合のみ、`--format jpg|pdf|tiff|png` を追加する。
7. シャッター音を抑制する必要がある場合は `--no-sound` を追加する。
8. ファイル保存時は、既定で同名の隣接メタデータJSONも作成される。不要な場合のみ `--no-metadata` を追加する。
9. クリップボード保存の場合は `python3 scripts/capture_macos_screenshot.py --mode clipboard` を実行し、ファイルは作成されないことを報告する。

**Step 4: 結果を確認する**
1. ファイル保存の場合は `stat [output-path]` または `file [output-path]` を実行し、成果物が存在し空でないことを確認する。
2. メタデータJSONが作成された場合は、画像パス、撮影モード、コマンド、ファイルサイズ、解決済みウィンドウIDが記録されていることを確認する。
3. クリップボード保存の場合は、可能であれば `osascript -e 'clipboard info'` を実行し、画像データが存在することを確認する。
4. 保存パス、メタデータパス、撮影モード、ユーザー操作が必要だったかどうかを報告する。
5. 目視確認が必要な場合は、利用可能な画像プレビューまたはファイル読み取りツールで保存先を確認する。

## よく使うコマンド

- 画面全体をファイルへ保存: `python3 scripts/capture_macos_screenshot.py --mode full --output outputs/screenshots/full.png`
- メインディスプレイを指定して保存: `python3 scripts/capture_macos_screenshot.py --mode full --display 1 --output outputs/screenshots/display-1.png`
- ウィンドウを対話式に選択: `python3 scripts/capture_macos_screenshot.py --mode window --output outputs/screenshots/window.png`
- アプリ名からウィンドウを自動検出して保存: `python3 scripts/capture_macos_screenshot.py --mode app-window --app Kaku --output outputs/screenshots/kaku.png`
- ウィンドウタイトルで絞って保存: `python3 scripts/capture_macos_screenshot.py --mode app-window --app Kaku --window-title Users --output outputs/screenshots/kaku-users.png`
- ウィンドウIDを指定して保存: `python3 scripts/capture_macos_screenshot.py --mode window-id --window-id 56523 --output outputs/screenshots/window-id.png`
- 範囲を対話式に選択: `python3 scripts/capture_macos_screenshot.py --mode selection --output outputs/screenshots/selection.png`
- 5秒後に画面全体を保存: `python3 scripts/capture_macos_screenshot.py --mode timed --delay 5 --output outputs/screenshots/timed.png`
- クリップボードへ保存: `python3 scripts/capture_macos_screenshot.py --mode clipboard`

## エラー対応

* `screencapture` が見つからない、または実行環境がmacOSではない場合は、このスキルがmacOS専用であることを報告して停止する。
* macOSが画面収録をブロックした場合は、システム設定でターミナルまたはホストアプリに「画面収録」権限を付与するよう案内し、その後同じコマンドを再実行する。
* 対話式の `window` または `selection` がタイムアウトした場合は、`--delay 2` を付けて再実行し、ウィンドウのクリックまたは範囲ドラッグが必要であることを説明する。
* 出力ファイルが空、または存在しない場合は、モードを変更する前に `--verbose` を付けて再実行し、stderrを確認する。全画面撮影で失敗した場合は `--display 1` を追加して再試行する。
* `app-window` で対象ウィンドウが見つからない場合は、対象アプリ名を確認し、必要ならアプリを起動してから再試行する。複数候補がある場合は `--window-title` で絞り込む。
* OCR、注釈、切り抜き、墨消し、画像編集が目的の場合は、必要に応じて先にスクリーンショットを取得し、その後に画像処理または文書処理のワークフローへ引き継ぐ。
