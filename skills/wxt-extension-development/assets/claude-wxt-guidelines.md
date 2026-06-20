# WXTプロジェクト向けガイドライン

- このプロジェクトはWXT製のブラウザ拡張である。
- UI は React、対象ブラウザは Chrome、messaging は webext-bridge を既定とする。
- `.wxt/` と `.output/` 配下の生成物を編集しない。
- 生成された `manifest.json` を直接編集しない。必要な変更は `wxt.config.*` またはentrypoint設定へ反映する。
- `browser.*`、`document`、`window` などの実行時APIをJS/TS entrypointのトップレベルで使わない。
- backgroundの実行時処理は `defineBackground` のコールバック内に置く。
- content scriptの実行時処理は `defineContentScript` の `main(ctx)` 内に置く。
- 変更はできるだけ小さくし、1回の作業では1つのentrypointに限定する。
- permissionsやhost permissionsを追加する場合は、各権限が必要な理由を説明する。
- 実装後は、明示的な禁止がない限り、`package.json` に定義されたbuild scriptを実行する。
- build結果、変更ファイル、生成manifestの変化、手動ブラウザ確認項目を報告する。
