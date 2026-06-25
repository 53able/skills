#!/usr/bin/env python3
"""macOS screencapture 用の小さなCLIラッパー。"""
import argparse
import datetime as dt
import json
import platform
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def default_output(fmt: str) -> Path:
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    return Path("outputs") / "screenshots" / f"screenshot-{stamp}.{fmt}"


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    i = 1
    while True:
        candidate = parent / f"{stem}-{i}{suffix}"
        if not candidate.exists():
            return candidate
        i += 1


def activate_app(app_name: str) -> None:
    subprocess.run(
        ["osascript", "-e", f'tell application "{app_name}" to activate'],
        text=True,
        capture_output=True,
        check=False,
    )


def list_windows() -> list[dict]:
    if shutil.which("swift") is None:
        raise RuntimeError("app-windowモードにはswiftコマンドが必要です。--mode window-id または --mode window を使ってください。")

    swift_code = r'''
import Foundation
import CoreGraphics
let options = CGWindowListOption(arrayLiteral: [.optionOnScreenOnly, .excludeDesktopElements])
guard let list = CGWindowListCopyWindowInfo(options, kCGNullWindowID) as? [[String: Any]] else { exit(1) }
for w in list {
    let id = w[kCGWindowNumber as String] as? Int ?? 0
    let owner = w[kCGWindowOwnerName as String] as? String ?? ""
    let name = w[kCGWindowName as String] as? String ?? ""
    let bounds = w[kCGWindowBounds as String] as? [String: Any] ?? [:]
    let x = bounds["X"] as? Int ?? 0
    let y = bounds["Y"] as? Int ?? 0
    let width = bounds["Width"] as? Int ?? 0
    let height = bounds["Height"] as? Int ?? 0
    let layer = w[kCGWindowLayer as String] as? Int ?? 0
    let alpha = w[kCGWindowAlpha as String] as? Double ?? 1.0
    let record: [String: Any] = [
        "id": id,
        "owner": owner,
        "name": name,
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "layer": layer,
        "alpha": alpha
    ]
    if let data = try? JSONSerialization.data(withJSONObject: record, options: []),
       let line = String(data: data, encoding: .utf8) {
        print(line)
    }
}
'''
    with tempfile.NamedTemporaryFile("w", suffix=".swift", delete=False, encoding="utf-8") as f:
        f.write(swift_code)
        swift_path = Path(f.name)
    try:
        proc = subprocess.run(["swift", str(swift_path)], text=True, capture_output=True)
    finally:
        swift_path.unlink(missing_ok=True)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or "swiftによるウィンドウ一覧取得に失敗しました。").strip())

    windows = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        try:
            windows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return windows


def resolve_app_window_id(app_name: str, title_filter: str | None = None) -> tuple[int, dict]:
    activate_app(app_name)
    windows = list_windows()
    app_key = app_name.lower()
    title_key = title_filter.lower() if title_filter else None
    candidates = []
    for w in windows:
        owner = str(w.get("owner", ""))
        title = str(w.get("name", ""))
        if app_key not in owner.lower() and app_key not in title.lower():
            continue
        if title_key and title_key not in title.lower():
            continue
        if int(w.get("width", 0)) <= 0 or int(w.get("height", 0)) <= 0:
            continue
        if int(w.get("layer", 0)) != 0:
            continue
        candidates.append(w)

    if not candidates:
        detail = f"アプリ名={app_name}"
        if title_filter:
            detail += f", タイトル条件={title_filter}"
        raise RuntimeError(f"対象ウィンドウが見つかりません: {detail}")

    selected = max(candidates, key=lambda w: int(w.get("width", 0)) * int(w.get("height", 0)))
    return int(selected["id"]), selected


def build_command(args, output: Path | None) -> list[str]:
    cmd = ["screencapture"]
    if args.no_sound:
        cmd.append("-x")
    if args.include_cursor:
        cmd.append("-C")
    if args.format:
        cmd.extend(["-t", args.format])
    if args.delay is not None:
        cmd.extend(["-T", str(args.delay)])
    if args.display is not None:
        cmd.extend(["-D", str(args.display)])

    if args.mode == "clipboard":
        cmd.append("-c")
        return cmd
    if args.mode == "window":
        cmd.extend(["-i", "-W"])
    elif args.mode == "window-id":
        if args.window_id is None:
            raise ValueError("window-idモードでは --window-id が必要です")
        cmd.extend(["-l", str(args.window_id)])
    elif args.mode == "app-window":
        if args.resolved_window_id is None:
            raise ValueError("app-windowモードではウィンドウIDの解決が必要です")
        cmd.extend(["-l", str(args.resolved_window_id)])
    elif args.mode == "selection":
        cmd.extend(["-i", "-s"])
    elif args.mode in {"full", "timed"}:
        pass
    else:
        raise ValueError(f"未対応のモードです: {args.mode}")

    if output is None:
        raise ValueError("ファイル保存の撮影では出力パスが必要です")
    cmd.append(str(output))
    return cmd


def write_metadata(args, output: Path, cmd: list[str]) -> Path:
    metadata_path = output.with_suffix(".json")
    if metadata_path.exists() and not args.overwrite:
        metadata_path = unique_path(metadata_path)
    stat = output.stat()
    payload = {
        "captured_at": dt.datetime.now().astimezone().isoformat(),
        "mode": args.mode,
        "output": str(output),
        "command": shlex.join(cmd),
        "file_size_bytes": stat.st_size,
        "display": args.display,
        "window_id": args.window_id,
        "app": args.app,
        "window_title_filter": args.window_title,
        "resolved_window_id": args.resolved_window_id,
        "resolved_window": args.resolved_window,
        "format": args.format or output.suffix.lstrip(".") or "png",
        "include_cursor": bool(args.include_cursor),
        "no_sound": bool(args.no_sound),
        "delay_seconds": args.delay,
    }
    metadata_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return metadata_path


def main() -> int:
    parser = argparse.ArgumentParser(description="macOSのスクリーンショットを再現可能な手順で取得する。", add_help=False)
    parser._optionals.title = "オプション"
    parser.add_argument("-h", "--help", action="help", help="ヘルプを表示して終了する。")
    parser.add_argument("--mode", choices=["full", "window", "window-id", "app-window", "selection", "clipboard", "timed"], required=True)
    parser.add_argument("--output", help="ファイル保存時の出力パス。")
    parser.add_argument("--delay", type=float, help="撮影前の遅延秒数。")
    parser.add_argument("--display", type=int, help="撮影対象ディスプレイ番号。例: 1")
    parser.add_argument("--window-id", type=int, help="window-idモードで撮影するmacOSウィンドウID。")
    parser.add_argument("--app", help="app-windowモードで撮影するアプリ名。例: Kaku")
    parser.add_argument("--window-title", help="app-windowモードで候補を絞り込むウィンドウタイトルの一部。")
    parser.add_argument("--format", choices=["png", "jpg", "pdf", "tiff"], help="screencaptureの出力形式。")
    parser.add_argument("--no-sound", action="store_true", help="スクリーンショット音を抑制する。")
    parser.add_argument("--include-cursor", action="store_true", help="対応環境でカーソルを含める。")
    parser.add_argument("--overwrite", action="store_true", help="既存の出力ファイルを上書きする。")
    parser.add_argument("--no-metadata", action="store_true", help="ファイル保存時の隣接メタデータJSONを作成しない。")
    parser.add_argument("--verbose", action="store_true", help="実行前にscreencaptureコマンドをstderrへ表示する。")
    args = parser.parse_args()
    args.resolved_window_id = None
    args.resolved_window = None

    if platform.system() != "Darwin":
        print("ERROR: このスクリプトはmacOS専用です。", file=sys.stderr)
        return 2
    if shutil.which("screencapture") is None:
        print("ERROR: screencaptureコマンドが見つかりません。", file=sys.stderr)
        return 2
    if args.window_id is not None and args.mode != "window-id":
        print("ERROR: --window-id は --mode window-id と一緒に指定してください。", file=sys.stderr)
        return 2
    if args.mode == "app-window" and not args.app:
        print("ERROR: app-windowモードでは --app が必要です。", file=sys.stderr)
        return 2
    if args.window_title and args.mode != "app-window":
        print("ERROR: --window-title は --mode app-window と一緒に指定してください。", file=sys.stderr)
        return 2

    if args.mode == "app-window":
        try:
            args.resolved_window_id, args.resolved_window = resolve_app_window_id(args.app, args.window_title)
        except RuntimeError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        if args.verbose:
            print(f"RESOLVED_WINDOW_ID: {args.resolved_window_id}", file=sys.stderr)

    output = None
    if args.mode != "clipboard":
        fmt = args.format or "png"
        output = Path(args.output) if args.output else default_output(fmt)
        output = output.expanduser()
        if not args.overwrite:
            output = unique_path(output)
        output.parent.mkdir(parents=True, exist_ok=True)

    try:
        cmd = build_command(args, output)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.verbose:
        print("COMMAND:", shlex.join(cmd), file=sys.stderr)

    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.returncode != 0:
        if proc.stdout:
            print(proc.stdout, file=sys.stdout, end="")
        if proc.stderr:
            print(proc.stderr, file=sys.stderr, end="")
        print(f"ERROR: screencaptureが終了コード {proc.returncode} で失敗しました。", file=sys.stderr)
        return proc.returncode

    if args.mode == "clipboard":
        print("SUCCESS: スクリーンショットをクリップボードへ保存しました。")
        return 0

    assert output is not None
    if not output.exists() or output.stat().st_size == 0:
        print(f"ERROR: 出力ファイルが作成されていないか空です: {output}", file=sys.stderr)
        return 1

    print(f"SUCCESS: スクリーンショットを保存しました: {output}")
    if not args.no_metadata:
        metadata_path = write_metadata(args, output, cmd)
        print(f"SUCCESS: メタデータを保存しました: {metadata_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
