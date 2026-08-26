# MCPガバナンス審査：[サーバー／ユースケース]

- **日付：** [YYYY-MM-DD]
- **審査者：** [氏名または役割]
- **責任者：** [業務責任者／サービス責任者]
- **配備方式：** [ローカルartifact／Managed remote]
- **判定：** [Go／Conditional Go／No-Go]
- **リスクtier：** [T0／T1／T2／T3]

## 経営判断

[判定、決定的な証拠、適用条件を3〜6文で記載する。]

## 審査範囲

- Server identity：
- Version、digest、endpoint：
- Toolとside effect：
- 利用者とtenant：
- Data class：
- 下流system：
- Credential：
- Filesystem accessとnetwork access：

## 確認した証拠

| 証拠 | 出典またはartifact path | 状態 | 注記 |
|---|---|---|---|
| | | Accepted／Rejected／Blocked | |

## リスク分類

- Classifier command：
- Classifier result：
- 発火条件：
- 不明項目：
- 必須統制：
- 例外／override：

## 信頼境界とデータフロー

[外部入力、秘密情報アクセス、cross-tool flow、外部送信、下流authorizationを記載する。]

## 統制審査

| 統制 | 必須 | 確認した証拠 | 状態 | 不足／是正 |
|---|---:|---|---|---|
| 管理者強制のallowlist | | | Pass／Fail／Blocked | |
| 最小権限credential | | | | |
| Token audience binding／passthrough禁止 | | | | |
| MCP process isolation | | | | |
| Filesystem restriction | | | | |
| Egress restriction | | | | |
| Approval gate | | | | |
| Auditability | | | | |
| Drift／change detection | | | | |
| Kill switch／revocation | | | | |

## 検証結果

| Test ID | 脅威／failure mode | 期待結果 | 観察結果 | 証拠path | 状態 |
|---|---|---|---|---|---|
| | | | | | Pass／Fail／Not run／Blocked |

## 判定条件

| 対応 | 責任者 | 期限 | Closeするgate |
|---|---|---|---|
| | | | |

## 残余リスク

- [リスク、影響資産、責任者、受容または失効日]

## 再審査条件

[この審査を無効にする変更を列挙する。]

## 出典

- [説明的な出典名](https://example.com)
