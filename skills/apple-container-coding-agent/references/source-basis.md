# 参照根拠

2026-08-26にagent-browserで参照先を確認した。同日、local hostではApple Container CLI／apiserver 1.2.2とserviceのrunning状態を確認した。main branchのWeb文書はinstalled releaseと異なる場合があるため、実行時はlocalの`--help`を正とする。

## 一次資料から確認した事項

- Appleは、各containerが個別のlightweight VMで動くと説明している。`container run`にはnon-root user、CPU／memory limit、capability drop、read-only root filesystem、bind mount、tmpfs、network、SSH Agent forwardingの制御がある。このskillではSSH forwardingを禁止し、networkなしをdefaultにする。
  - https://github.com/apple/container/blob/main/docs/technical-overview.md
  - https://github.com/apple/container/blob/main/docs/command-reference.md
- Appleはbind mountをhostとの共有として説明し、`readonly` mount、named volume、VM memory上のtmpfsを文書化している。これはprivate workspaceとread-only inputのpatternを支えるが、明示的に共有したpathのriskは除去しない。
  - https://github.com/apple/container/blob/main/docs/volumes.md
- Anthropicはpermissionとisolationを区別している。現行sandbox guideでは、write可能なproject mountはhost codeを変更でき、network egressは読めるdataを流出させ得る。またsandboxはmodelへ送られる内容を変えない。未信頼repositoryにはdedicated VMを推奨している。
  - https://code.claude.com/docs/en/sandbox-environments
- Anthropicの現行programmatic usage文書では、`claude -p --bare`がhook、skill、command、subagent、plugin、MCP server、auto memory、`CLAUDE.md`の自動検出を止める。またbare modeはOAuth credentialとsystem Keychainを使わず、明示的なprovider認証を必要とする。
  - https://code.claude.com/docs/en/headless
- OpenAIの現行non-interactive文書では`codex exec`を使い、明示的sandbox、`--ephemeral`、`--ignore-user-config`、`--ignore-rules`、`--json`を提供している。またrepository管理下のcodeが読めるjob scopeへAPI keyを置かないよう警告している。
  - https://learn.chatgpt.com/docs/non-interactive-mode.md
- Piはproject trustがsandboxではなく、toolとextensionがPi processのOS権限で動くと説明している。未信頼または無人の作業にはcontainer／VMを使い、より強い保護にはread-only mountまたはcopy-in／copy-outを推奨する。hostの`~/.pi/agent`をmountするとsettings、session、credentialが公開されるとも警告している。
  - https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/security.md
  - https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/containerization.md
  - https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/usage.md

## 設計の出典

このskillは、次のsourceにある境界modelと制約を実行手順へ変換した。

- `/Users/tadano-go/reps/53able/blog/outputs/claude-supervisor-worker.md`

local absolute pathはprivate skill内のprovenanceとしてのみ保持する。公開artifactではrepository-relative pathまたはpublic URLへ置き換える。
