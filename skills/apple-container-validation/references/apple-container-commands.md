# Apple Containerコマンド参照

本ファイルはローカル検証時の補助であり、CLIの現行仕様を保証しない。必ず `container <subcommand> --help` を優先する。

2026-08-15に `container CLI version 1.2.2` で確認した代表コマンド:

```bash
container --version
container system status
container system start
container image list
container build --progress plain -t IMAGE -f Containerfile CONTEXT
container run --rm --init --name NAME \
  --network none \
  --cpus 1 \
  --memory 2G \
  --read-only \
  --tmpfs /tmp \
  --mount type=bind,source=/absolute/input,target=/workspace,readonly \
  --mount type=bind,source=/absolute/output,target=/evidence \
  IMAGE command arg
container logs NAME
container stats NAME
container kill NAME
container delete --force NAME
container inspect NAME
container image inspect IMAGE
```

## 注意点

- Apple ContainerはmacOS上でLinuxコンテナを実行する。macOSネイティブGUIの再現環境ではない。
- `container run` の引数はイメージ名より前をランタイムオプション、後ろをコンテナ内コマンドとして扱う。
- `--network none` を既定にし、通信が必要なケースだけ明示的に変更する。
- `--read-only` と `--tmpfs /tmp` を組み合わせ、証跡だけを `/evidence` へ書く。
- タイムアウト後にコンテナが残った場合だけ、対象名を指定して `container delete --force NAME` を使う。`--all` は使わない。
- コンテナ起動には仮想マシン初期化コストがある。スモーク後に独立ケースを並列化する。
- arm64以外が必要な場合は `--platform` と必要に応じて `--rosetta` を検討し、使用有無を来歴へ残す。

## 公式資料

- Repository: https://github.com/apple/container
- How-to: https://github.com/apple/container/blob/main/docs/how-to.md
- Technical overview: https://github.com/apple/container/blob/main/docs/technical-overview.md
