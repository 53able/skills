# 検証ハーネスの実装規約

PythonまたはJavaScript/TypeScriptで検証ハーネスを新規作成・変更するときだけ本ファイルを読む。対象リポジトリに既存の規約がある場合は、その規約との衝突を記録し、無断で全面移行しない。

## Python

### 依存管理

- Python依存が1つでもある場合は`uv`で管理する。
- `requirements.txt`への手書き追加や、ホスト環境への直接`pip install`を行わない。
- `pyproject.toml`と`uv.lock`を検証入力へ含め、両方のSHA-256を来歴へ記録する。
- ロック済み環境の再現には`uv sync --frozen`を使う。
- コマンド実行には`uv run`を使う。

```bash
uv init --bare
uv add pytest httpx
uv lock
uv sync --frozen
uv run pytest -q
```

依存がない標準ライブラリだけの単体スクリプトは`python3`で実行してよい。後から外部依存を追加する時点で`uv`管理へ移す。

### Containerfile

`uv.lock`と`pyproject.toml`を先にコピーし、依存レイヤーをキャッシュする。`uv`の導入方法は実行時点の公式ドキュメントで確認し、バージョンを固定する。

```Dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY . .
CMD ["uv", "run", "pytest", "-q"]
```

## JavaScript / TypeScript

### 固定スタック

- JavaScriptの検証ハーネスはTypeScriptで実装する。
- TypeScriptはメジャーバージョン7を使用し、`package.json`とlockfileでは実際に検証した版へ固定する。
- 実行ランナーは`tsx`を使う。
- 構造化ロガーは`pino`を使う。
- `package-lock.json`を保存し、コンテナ内では`npm ci`を使う。

```bash
npm install --save-exact typescript@7 tsx pino
npm ci
npx tsc --noEmit
npx tsx src/run.ts
```

`typescript@7`がレジストリ上で解決できない場合は推測した版へ落とさず、`Blocked`として利用可能な版とエラーを記録する。

### pinoの使い方

自由形式の`console.log`だけに依存せず、検索・集計可能なイベントを出す。

```ts
import pino from "pino";

const logger = pino({
  level: process.env.LOG_LEVEL ?? "info",
  base: { component: "validation-runner" },
});

const jobLogger = logger.child({ runId, caseId, attempt });
jobLogger.info({ event: "case_started" }, "Starting validation case");
jobLogger.info(
  { event: "case_completed", durationMs, status },
  "Completed validation case",
);
```

最低限、次のフィールドをイベントへ含める。

- `event`
- `runId`
- `caseId`
- `attempt`
- `durationMs`
- `status`
- エラー時の`err`

オラクルがstdoutを評価する場合、pinoログが判定対象へ混ざらないよう、ログをstderrまたは専用ログファイルへ分離する。秘密値、トークン、認証ヘッダーをログへ出さない。

### Containerfile

依存ファイルを先にコピーし、`npm ci`でlockfileどおりに復元する。

```Dockerfile
FROM node:22-slim
WORKDIR /app
COPY package.json package-lock.json tsconfig.json ./
RUN npm ci
COPY src ./src
RUN npm run typecheck
CMD ["./node_modules/.bin/tsx", "src/run.ts"]
```

## 来歴

Pythonでは`pyproject.toml`と`uv.lock`、TypeScriptでは`package.json`、lockfile、`tsconfig.json`をbuild contextへ含める。`run-manifest.json`のbuild context hashにより、依存やコンパイラ設定の変更を別実験として扱う。
