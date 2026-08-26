# MCPリスクモデル

このモデルを保守的なガバナンス分類に使用する。法令適合や認証取得の判定には使用しない。

## 判定順序

すべての項目をbooleanで評価する。欠落または`null`の項目は不明とし、T0へ分類する。

1. T0 blockerを評価する。一つでもtrueならT0とする。
2. T0がなければT3 triggerを評価する。一つでもtrueならT3とする。
3. T3がなければT2 triggerを評価する。一つでもtrueならT2とする。
4. T1の全条件を満たす場合だけT1とする。
5. 既知の値がどの条件にも一致しない場合は、保守的にT2とする。

優先順位は`T0 > T3 > T2 > T1`とする。

## 該当なしの正規化

すべての項目を埋める。機能が存在しない場合は、次の値を使う。

- 資格情報を使わない場合は、`principal_bound_credential=true`、`shared_admin_credential=false`、`admin_credential=false`、`broad_scope_credential=false`、`personal_scoped_credential=false`とする。
- 副作用のある操作がない場合は、`side_effecting_action=false`とし、3つの副作用ログ項目を該当なしの安全条件として`true`にする。
- 高影響機能がない場合は、`high_impact_capability=false`、`high_impact_policy_blockable=true`とする。
- `deployment_identity_known=true`は、不変のローカルartifact identityまたは正規のmanaged remote endpoint identityを証拠で確認した場合だけ設定する。
- 入手できない証拠を「該当なし」へ変換しない。

## T0 blocker

- Publisher identityが不明である。
- Artifact identityまたはremote endpoint identityが不明である。
- 任意shellを実行できる。
- Host filesystemのreadが無制限である。
- Host filesystemのwriteが無制限である。
- 共有administrator credentialを使う。
- Credentialをprincipalへ結び付けられない。
- 任意egressが可能である。
- 副作用のある操作でactor、target、result statusのいずれかを記録できない。
- 高影響の操作を決定論的なpolicyで停止できない。

## T3 trigger

- Secretへアクセスする。
- 規制対象dataへアクセスする。
- 破壊的操作を行う。
- 支払いを行う。
- 本番環境を変更する。
- 非公開dataを外部へ送信する。
- Administrator credentialを使う。
- 広域scopeのcredentialを使う。
- Critical serviceへ影響する。
- 複数tenantへ影響する。
- 組織全体へ影響する。
- 不可逆操作を行う。

## T2 trigger

- 社内の非規制dataを読む。
- 限定的で可逆なwriteを行う。
- Allowlist済みの外部APIを使う。
- Principalへ結び付いた限定scopeのcredentialを使う。
- Team単位で影響する。
- 上限と期限を強制した非破壊的な自動処理を行う。

## T1条件

次のすべてを満たす。

- 公開された非機密dataだけを使う。
- Resourceを限定したread-only accessである。
- 利用者が一人である。
- 対象resourceが非criticalである。
- 副作用がない。

## Tier別の必須統制

### T1

- 正規のsourceまたはendpoint identity。
- 固定versionまたは文書化されたremote変更履歴。
- 接続時と変更時の承認。
- Actor、server、tool、decision、result statusのログ。

### T2

- T1の全統制。
- DigestとSBOM、またはmanaged remoteの変更通知とdrift検知。
- Principalへ結び付いた短命・限定scopeのcredential。
- Writeと外部callの引数単位承認。
- Rate、scope、destination、durationの上限。
- Correlation IDとpolicy versionのログ。
- Negative attack testとkill-switch test。

### T3

- T2の全統制。
- 署名済みprovenance、または同等の契約・技術統制。
- Callごとの承認または二者承認。
- Just-in-time privilegeとblast-radius上限。
- 下流操作、recipient、destinationの追跡。
- 全社即時停止とtoken失効。
- SecurityとData Ownerによる独立承認。

## 証拠ルール

強制可能な設定、policy、テスト結果、直接観察のいずれかが裏付ける場合だけ、統制を実装済みと判定する。機能を説明する文書だけでは、その機能が審査対象環境で有効か、回避不能かを証明できない。
