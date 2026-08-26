# MCPガバナンスの証拠要件

現在の審査に必要な節だけを読む。

## 申請時の証拠

- 業務目的と責任者。
- 利用者数と影響するtenant。
- Data classificationと外部送信経路。
- MCPサーバーの完全なidentity：publisher、repository、packageまたはimage、versionまたはdigest、commandまたはcanonical URL。
- Toolのname、description、input／output schema、annotation、fingerprint。
- Credentialのissuer、audience、scope、expiry、storage、principal binding。
- Filesystem mountとnetwork destination。
- 下流systemと不可逆操作。
- Approval policy、audit path、kill switch、rollback、廃止責任者。

## ローカル／配布artifactの証拠

- Canonical repositoryとpublisher ownership。
- 不変のversion、package digest、image digest、binary hash。
- Lockfile、dependency、SBOM、install script、dynamic download。
- Tierが要求するsignatureまたはprovenance。
- Sandbox profile、filesystem mount、environment variable、OS user、egress policy。
- 緊急blockとrollbackの手順。

## Managed remote serviceの証拠

- Canonical HTTPS endpointとserver identity。
- Authenticationとauthorization flow。
- 変更通知とincident通知の約束。
- Versioned endpointまたは文書化された変更履歴。
- Tool definitionとschema driftの検知。
- 限定scope、destination、data retention、subprocessor。
- Runtime monitoringと即時停止。
- 利用終了、credential失効、data削除の手順。

## 実行時の証拠

- 利用者やworkspaceが緩和できないmanaged server allowlist。
- Tool単位のdeny／ask／allow policy。
- Request単位のissuer、audience、resource、scope、expiry検証。
- 分離した下流credentialとclient-token passthrough禁止。
- Host shell sandboxだけに依存しないMCP server processの隔離。
- Filesystemとegressのnegative test。
- Server、tool、argument、target、destination、side effectを示す承認画面。
- Actor、server、tool、policy、approval、result status、downstream actionを結ぶaudit record。

## 変更時の証拠

次のいずれかが変わったら再審査する。

- Publisher、owner、repository、package、image、version、digest、signature。
- Command、argument、URL、transport、protocol version。
- Tool name、description、schema、annotation、capability。
- OAuth issuer、scope、credential type、storage。
- Filesystem mount、network destination、data class、retention、subprocessor。
- Readからwrite、writeからdestructive、single-userからbroad-useへの変更。

## 検証時の証拠

各テストで次を記録する。

- Test IDと脅威／failure mode。
- Environmentと審査対象version。
- Preconditionsと正確なinput。
- Expected result。
- Observed result。
- Artifactまたはlog path。
- `Pass`、`Fail`、`Not run`、`Blocked / Unverified`のいずれか。

## 一次資料

- MCP Specification: https://modelcontextprotocol.io/specification/2026-07-28
- MCP Authorization Security Considerations: https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/security-considerations
- MCP Security Best Practices: https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices
- MCP Tools: https://modelcontextprotocol.io/specification/2026-07-28/server/tools
- MCP Registry: https://modelcontextprotocol.io/registry/about
- OWASP MCP Security Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/MCP_Security_Cheat_Sheet.html
- NIST AI RMF Playbook: https://airc.nist.gov/airmf-resources/playbook/govern/
- CISA Secure by Demand: https://www.cisa.gov/resources-tools/resources/secure-demand-guide
- SLSA Artifact Verification: https://slsa.dev/spec/v1.2/verifying-artifacts
