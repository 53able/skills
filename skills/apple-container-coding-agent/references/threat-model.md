# 脅威モデルと信頼境界

network access、credential、patchのtrusted repositoryへの取り込みを有効にする前に読む。

## 保護対象

- host working treeとGit metadata
- host home、SSH Agent、Keychain由来情報、cloud credential、container socket
- Git remoteへのwrite、package publish、deploy、本番変更の権限
- 承認記録とhost-side evidence

## 未信頼入力

- repository file、dependency script、build出力、model出力、agent transcript、Worker生成evidence
- `AGENTS.md`、`CLAUDE.md`、`.mcp.json`、`.claude/`、`.codex/`、`.pi/`、hook、plugin、skill、extensionなどのautoload入力
- 返却されたpatchそのもの

## 必須の境界

1. 権限を決定論的なhost-side codeへ置く。成功、retry、merge、push、deployをWorkerに決めさせない。
2. tracked-file snapshotからWorker workspaceを作る。host working treeをread-writeでbind mountしない。
3. host home、SSH Agent、cloud設定、Git credential、package credential、Apple Container制御socketをWorkerへ渡さない。
4. Workerのlogとmanifestを自己申告として扱う。patch、changed path、hash、test結果をWorker外で再計算する。
5. quarantine cloneだけにpatchをapplyする。人間の承認を求める前にfresh環境でacceptance checkを再実行する。
6. 承認をbaseline commit、canonical patch hash、resulting tree hash、target ref、policy／check digest、expiryへ結びつける。

## networkの制約

Apple Containerの`--network`はcontainerをnetworkへ接続するoptionであり、hostname allowlistとしては文書化されていない。したがって`network.mode: restricted`には、Worker外部で強制されるgateway、firewall、proxy policyが必要になる。この制御がない場合は、無制限networkで代替せず、`BLOCKED: restricted egress not enforced`と記録する。

gatewayはupstream credentialを隠せるが、agentが読めるsourceやsecretを正規のmodel requestで送ることまでは防げない。実行前にsnapshotからsecretを除き、model provider向けのdata classification policyを別途適用する。

## credentialの制約

Workerから見えるtokenは、有効期間中はcredentialである。短命、run-bound、audience制約付きのgateway tokenとserver-side budgetを優先する。host SSH Agent、長命なcloud／Git administrator credentialをmountしない。credentialをimage、task contract、log、patch、evidence bundleへ保存しない。

## 対象外

このworkflowは到達可能なattack surfaceを狭める。VM escape、runtime vulnerability、provider側のdata exposure、prompt injection、supply-chain compromise、明示的に共有したmountやnetworkの欠陥がないことは証明しない。
