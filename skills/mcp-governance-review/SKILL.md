---
name: mcp-governance-review
description: MCPサーバーとツールの導入を、決定論的なガバナンス手順で審査する。T0〜T3のリスク分類、来歴、権限、ネットワーク、承認ゲート、監査証跡、変更管理、インシデント対応、Go／Conditional Go／No-Go判定に使用する。ペネトレーションテスト、マルウェア実行、法令適合の認証、製品固有のセキュリティ試験の代替には使用しない。
---

# MCPガバナンス審査

## 手順

**ステップ1：審査範囲を固定する**
1. MCPサーバー、配備方式、ユースケース、利用者、データ分類、ツール、下流システム、資格情報、ファイルアクセス、通信先を特定する。
2. 配布元、配布物、接続先、ツール定義、スコープ、通信先、承認ポリシーの変更を、新しい審査範囲として扱う。
3. `assets/intake-template.json`を複製し、すべての`null`を証拠に基づく`true`または`false`で埋める。不明な値を推測しない。

**ステップ2：証拠を収集する**
1. `references/evidence-requirements.md`を読み、配備方式とライフサイクル段階に必要な証拠を集める。
2. 公式仕様、ベンダー文書、ソースリポジトリ、パッケージメタデータ、アドバイザリ、SBOM、署名、設定エクスポート、ポリシーファイル、テストログを優先する。
3. 観察した事実と審査者の推論を分ける。到達不能、入手不能、未試験の証拠は`Blocked / Unverified`と記録する。

**ステップ3：リスクを決定論的に分類する**
1. リスク入力を変更する前に`references/risk-model.md`を読む。
2. `python3 scripts/classify-risk.py --input <completed-intake.json> --format text`を実行する。
3. `python3`が設定されていない場合は、利用可能なPython 3実行ファイルを明示して実行する。分類ロジックを手作業で変更しない。
4. 欠落、`null`、非booleanのリスク項目は、修正するまでT0として扱う。
5. スクリプトが返した発火条件と必須統制をすべて記録する。

**ステップ4：必須統制を審査する**
1. 管理者強制のサーバー許可リスト、最小権限の資格情報、トークンのaudience binding、token passthrough禁止、MCPプロセス隔離、ファイル制限、egress制御、承認ゲート、監査可能性、変更検知、kill switchを確認する。
2. ホスト側のshell sandboxとMCPサーバープロセスの隔離を区別する。
3. ローカル／配布物とmanaged remote serviceを分ける。
   - ローカル／配布物には、不変のバージョンまたはダイジェスト管理と緊急失効を要求する。
   - managed remote serviceには、正規の接続先、変更通知、ツール定義の差分検知、限定スコープ、実行時監視、即時停止を要求する。
4. Registry掲載、ツール注釈、roots、ignoreファイル、モデルalignmentを、セキュリティ境界ではなく補助情報として扱う。

**ステップ5：検証ケースを定義する**
1. 特定した脅威から攻撃テストを作る。不正なissuer、audience、scope、expiry、tool poisoning、shadowing、name collision、間接prompt injection、schema drift、command injection、SSRF、秘密情報アクセス、禁止egress、直接JSON-RPC迂回を含める。
2. timeout、retry上限、policy engine停止、ログ停止、token失効、kill switch、rollbackの耐障害テストを追加する。
3. 各テストの期待結果と証拠パスを明記する。実行していないテストを合格と記録しない。

**ステップ6：判定を確定する**
1. 次のいずれか一つを選ぶ。
   - `No-Go`：T0 blockerが残る、高影響機能の必須証拠がない、または操作を停止・調査できない。
   - `Conditional Go`：T1〜T3の統制は設計済みだが、本番拡大前に期限付きの是正事項が残る。
   - `Go`：必須統制を実装し、negative testに合格し、残余リスクの責任者を定め、緊急停止を実証した。
2. ツール説明、注釈、評判、Registry掲載、確認ダイアログだけを根拠にtierを下げない。
3. tier例外にはSecurityとData Ownerの承認、代替統制の証拠、失効日を要求する。

**ステップ7：審査成果物を書く**
1. `assets/review-report-template.md`の構成を複製する。
2. 範囲、証拠、リスク分類、発火条件、信頼境界、統制不足、テスト結果、判定、是正責任者と期限、残余リスク、再審査条件、出典リンクを含める。
3. 数字だけの引用記号ではなく、説明的な直接リンクを使う。
4. 未実行テストを`Not run`、入手不能な証拠を`Blocked / Unverified`と記録する。

**ステップ8：提出前に検証する**
1. 保存済みintakeへ`classify-risk.py`を再実行し、レポートのtierがstdoutと一致することを確認する。
2. 重要な主張、テスト結果、判定条件がURLまたは成果物パスへ結び付いていることを確認する。
3. 公開文書にローカル絶対パスが含まれないことを確認する。
4. 対応する証拠がない主張へ「検証済み」「再現済み」「合格」を使わない。

## エラー処理

- intakeが未完成ならT0を維持し、不明項目をすべて列挙する。安全側の値を推測しない。
- classifierが型を拒否したら、複製したintakeを修正して再実行する。
- 製品文書と観察結果が食い違う場合は、対象バージョンで観察した証拠を優先し、文書との差分を記録する。
- remote serviceがartifact provenanceを提示できない場合は、managed remote向け代替統制を適用する。artifactを固定したと記載しない。
- 必須テストを安全に実行できない場合は`Blocked / Unverified`と記録し、安全な試験環境を定義する。条件に応じてNo-GoまたはConditional Goを維持する。
