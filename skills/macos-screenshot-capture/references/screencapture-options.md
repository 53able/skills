# screencapture オプション参照

正確な `screencapture` フラグが必要な場合だけ、このファイルを読む。

## 主要モード

- 画面全体をファイルへ保存: `screencapture path.png`
- ディスプレイを指定して保存: `screencapture -D 1 path.png`
- ウィンドウを対話式に選択: `screencapture -i -W path.png`
- アプリ名からウィンドウIDを自動検出して保存: ヘルパーの `--mode app-window --app Kaku` を使う。
- ウィンドウIDを指定して保存: `screencapture -l 56523 path.png`
- 範囲を対話式に選択: `screencapture -i -s path.png`
- クリップボードへ保存: `screencapture -c`
- タイマー撮影: `screencapture -T 5 path.png`
- シャッター音を抑制: `screencapture -x path.png`
- 対応環境でカーソルを含める: `screencapture -C path.png`
- 形式を指定: `screencapture -t png path.png`

## 補足

- `-i` は対話式撮影を開始する。
- `-D` は撮影対象ディスプレイ番号を指定する。通常の全画面撮影が失敗する場合の再試行にも有効。
- `-W` は対話式のウィンドウ撮影を開始する。macOS上で対象ウィンドウをクリックする必要がある。
- `-l` はウィンドウIDを指定して対話なしで撮影する。ウィンドウIDはCoreGraphicsなどで取得する。
- ヘルパーの `app-window` モードは、Swift/CoreGraphicsで表示中ウィンドウ一覧を取得し、アプリ名に一致する最大面積の通常ウィンドウを `-l` に渡す。
- `-s` は対話式の範囲撮影を開始する。macOS上で範囲をドラッグする必要がある。
- `-c` はファイルではなくクリップボードへ書き込む。
- `-T` は秒数指定の遅延撮影に使う。メニューを開く、ウィンドウを整えるなどの準備時間が必要な場合に有効。
- 近年のmacOSでは、ターミナルアプリやホストアプリに「画面収録」権限が必要になる場合がある。
