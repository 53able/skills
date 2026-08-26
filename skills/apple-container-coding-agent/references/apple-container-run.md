# Apple Containerの実行pattern

このfileは固定されたcommand仕様ではなくpatternとして使う。localの`container run --help`を実行し、installed CLIをこのreferenceより優先する。

## preflight

```bash
container --version
container system status
container run --help
container image inspect <pinned-image>
```

serviceの起動、imageのpull、imageのbuildがhost状態を変更するかnetworkを使う場合は、operatorの許可なく実行しない。

## offline smoke test

最初は`--network none`を使う。準備済みinputをread-onlyでmountする。privateなwrite可能workspaceにはtmpfsまたはcontainer-private named volumeを使う。read-write mountはevidence directoryだけにする。evidence directoryはrepository外にmode `0700`で作成する。world-writableにせずnon-root guestからbind mountへ書き込めるよう、Workerを`WORKER_UID=$(id -u)`でbuildする。

```bash
container run --rm --init \
  --name <unique-run-name> \
  --network none \
  --cpus 2 \
  --memory 4G \
  --read-only \
  --cap-drop ALL \
  --tmpfs /tmp:size=512M,mode=1777 \
  --env HOME=/tmp/agent-home \
  --tmpfs /workspace:size=4G,mode=0777 \
  --mount type=bind,source=<absolute-run-input>,target=/run,readonly \
  --mount type=bind,source=<absolute-evidence>,target=/evidence \
  --user <image-non-root-user> \
  <pinned-image> <operator-owned-entrypoint>
```

`--ssh`、`--publish-socket`、`--virtualization`、広範なenv file、host home mountを指定しない。監査対象runでmutableな未固定image tagを使わない。

## networkを使うagent run

model-backed CLIは通常networkを必要とする。Apple Containerの`--network`はhostname egress allowlistとして文書化されていない。`--network none`を変更する前に、Worker外部のgatewayまたはnetwork policyが宛先を制限することを確認する。この制御がなければ、`BLOCKED: restricted egress not enforced`で停止する。

agent invocationに必要な短命run tokenだけを渡す。repository commandからWorkerの環境変数を読める前提で扱う。未信頼build／test scriptと同じprocess environmentへ長命なupstream provider keyを公開しない。

## workspace初期化

VM内で次を行う。

1. `/run/snapshot.tar`をprivateな`/workspace`へ展開する。
2. remoteを持たないlocal Git repositoryを初期化する。
3. operator所有の一時identityで展開済みbaselineをcommitする。
4. 選択したagent adapterを`/workspace`から実行する。
5. agent eventとprocess exit statusを`/evidence`へ保存する。ただしWorkerの自己申告として扱う。
6. `git diff --binary HEAD`を`/evidence/candidate.patch`として生成する。
7. Workerを停止する。push、deploy、編集済みworkspaceのhostへのcopyを行わない。

## host-side collection

host orchestratorでargv、cwd、開始／終了時刻、exit code、raw stdout／stderr、timeout／kill理由、container／image identity、task-contract hash、snapshot hashを取得する。収集後にevidenceをhash化する。Workerが生成した`status.json`をtrusted provenanceとして扱わない。

## cleanup

timeoutまたは失敗後は、一意に命名したrun containerだけを削除する。このworkflowで広範な`--all`やprune commandを使わない。cleanup前にevidence directoryを保存する。
