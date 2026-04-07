# 認知負荷パターン カタログ

認知負荷の種類と、それを下げるためのリファクタリングパターンを定義する。

## 認知負荷の種類

| 種類 | 定義 | 対処 |
|------|------|------|
| **固有的負荷 (Intrinsic)** | タスクそのものの難易度。削減不可。 | — |
| **外来的負荷 (Extraneous)** | 情報の提示方法や設計の癖によるもの。削減可能。 | 本カタログで対処 |

ヒューマンの作業記憶は約4チャンク。`🤯` はそれを超えた状態を示す。

---

## Pattern 1: 中間変数による条件式の分解

**問題 (🤯)**
```
if val > someConstant
    && (condition2 || condition3)
    && (condition4 && !condition5) {
```

**解決 (🧠)**
```
isValid   = val > someConstant
isAllowed = condition2 || condition3
isSecure  = condition4 && !condition5

if isValid && isAllowed && isSecure {
```

**原則:** 意味のある名前を持つ中間変数で条件を分解し、読み手が条件を記憶しなくていい状態にする。

---

## Pattern 2: アーリーリターンによるネスト解消

**問題 (🧠+++)**
```
if isValid {
    if isSecure {
        stuff
    }
}
```

**解決 (🧠)**
```
if !isValid  { return }
if !isSecure { return }

stuff  // ここに到達したら前提条件はすべて満たされている
```

**原則:** ハッピーパスに集中する。前提条件はガード節でアーリーリターンし、ネストを排除する。

---

## Pattern 3: 深いモジュール vs 浅いモジュール

**浅いモジュール (危険)**
```
// インタフェースは複雑、機能は微小
MetricsProviderFactoryFactory
UserRepositoryInterfaceAdapterImpl
```

**深いモジュール (理想)**
```
// シンプルなインタフェース、複雑な実装を隠蔽
open(path, flags, permissions)
read(fd, buffer, count)
write(fd, buffer, count)
```

**原則:** Unix I/O のように、強力な機能を持ちながらインタフェースはシンプルに保つ。
モジュール数が多いほど、相互作用の記憶コストが上がる。

---

## Pattern 4: 継承よりコンポジション

**問題 (🤯)**
```
AdminController
  extends UserController
    extends GuestController
      extends BaseController
```
各クラスを読み解かないと AdminController の動作が把握できない。
SuperuserController が AdminController を継承していれば連鎖的に壊れる可能性もある。

**解決**
コンポジションで必要な機能だけを組み合わせる。継承ツリーを垂直に追う認知コストを排除する。

---

## Pattern 5: 自己記述的なステータスコード

**問題 (🧠+++)**
```
401 -> expired JWT
403 -> not enough access
418 -> banned users
```
フロントエンド・QA が毎回このマッピングを記憶しなければならない。

**解決 (🧠)**
```json
{ "code": "jwt_has_expired" }
{ "code": "insufficient_permissions" }
{ "code": "user_banned" }
```

**原則:** ビジネスの意味を HTTP ステータスコードに乗せない。レスポンスボディで自己記述する。

---

## Pattern 6: DRY の過剰適用を避ける

**問題**
関係のないコンポーネント間で共通化を強行 → 密結合 → 一箇所の変更が予期せぬ場所を壊す (🤯)

**原則 (Rob Pike)**
> A little copying is better than a little dependency.

早すぎる抽象化は将来の変更を困難にする。コピーと依存のトレードオフを明示的に評価する。

---

## Pattern 7: フレームワークを外側に置く

**問題**
ビジネスロジックがフレームワークのマジックに深く依存 → 新メンバーはフレームワークを数ヶ月学ばないと貢献できない (🤯)

**解決**
フレームワークをライブラリとして使う。コアロジックはフレームワークのコンポーネントを使うが、フレームワークに依存しない形で書く。

---

## Pattern 8: レイヤードアーキテクチャの費用対効果

**費用** (毎回支払う)
- 抽象レイヤーを作業記憶に保持する必要がある
- コールスタックをジャンプして追跡するコストが指数的に増える

**便益** (稀にしか享受しない)
- コアロジックをインフラから分離してテストできる
- ストレージ交換が楽（実際は交換コストの数%しか節約できない）

**原則:** レイヤーは実用的な理由があるときだけ追加する。アーキテクチャのためのレイヤーは作らない。
