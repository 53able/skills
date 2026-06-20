# WXT実務ガイド

この参照は、WXT開発時に仕様確認が必要な場合だけ読む。

## 主要概念

- WXTはWeb Extension開発のためのフレームワークで、主要ブラウザ、TypeScript、Vite、HMR、ファイルベースentrypointを扱う。
- WXTは拡張APIそのものの代替ではない。Chrome / Mozillaの拡張API仕様は別途確認する。
- `manifest.json` は基本的に手書きしない。`wxt.config.*`、entrypoint設定、modules、hooksからWXTが生成する。
- build後の生成manifestは `.output/{target}/manifest.json` に出る。

## 初期化とscripts

代表的な初期化コマンド:

```bash
npm create wxt@latest
npx wxt@latest init
pnpm dlx wxt@latest init
bunx wxt@latest init
```

代表的なscripts:

```json
{
  "scripts": {
    "dev": "wxt",
    "dev:firefox": "wxt -b firefox",
    "build": "wxt build",
    "build:firefox": "wxt build -b firefox",
    "zip": "wxt zip",
    "zip:firefox": "wxt zip -b firefox",
    "postinstall": "wxt prepare"
  }
}
```

実際には必ず対象プロジェクトの `package.json` を読む。

## 標準構成

```text
{rootDir}/
  .output/
  .wxt/
  assets/
  components/
  entrypoints/
  public/
  utils/
  app.config.ts
  package.json
  tsconfig.json
  web-ext.config.ts
  wxt.config.ts
```

`srcDir: 'src'` が設定されている場合、`entrypoints/` や関連ディレクトリが `src/` 配下に移ることがある。

## entrypoint例

```text
entrypoints/
  background.ts
  popup.html
  options.html
  content.ts
  youtube.content.ts
```

ディレクトリ形式:

```text
entrypoints/
  popup/
    index.html
    main.ts
    style.css
  youtube.content/
    index.ts
    style.css
```

注意点:

- entrypointの自動発見は0階層または1階層を前提にする。
- 補助ファイルを `entrypoints/` 直下に置くと、意図せず別entrypointとして扱われる可能性がある。

## background

```ts
import { browser } from 'wxt/browser';

export default defineBackground(() => {
  browser.action.onClicked.addListener(() => {
    // runtime code
  });
});
```

## content script

```ts
export default defineContentScript({
  matches: ['https://example.com/*'],
  main(ctx) {
    console.log('content script loaded');
  },
});
```

トップレベルで `browser.*`、`document`、`window` を呼ばない。WXTはbuild時にentrypointをNode.js環境で読み込む。

## manifestとpermissions

```ts
export default defineConfig({
  manifest: {
    permissions: ['storage'],
    host_permissions: ['https://example.com/*'],
  },
});
```

permissionsは最小化する。対象ブラウザ、manifest version、実際に使うAPIによって必要権限が異なる。

## content script UI

- `createIntegratedUi`: ページDOMへ統合。CSSやイベントの分離は弱い。
- `createShadowRootUi`: Shadow RootでCSS分離。一般的な挿入UIの第一候補。
- `createIframeUi`: iframeで強く分離。HMRや独立UIに向くが、設定が増える。

Shadow Root例:

```ts
import './style.css';

export default defineContentScript({
  matches: ['https://example.com/*'],
  cssInjectionMode: 'ui',
  async main(ctx) {
    const ui = await createShadowRootUi(ctx, {
      name: 'example-ui',
      position: 'inline',
      anchor: 'body',
      onMount(container) {
        const app = document.createElement('div');
        app.textContent = 'Hello from WXT';
        container.append(app);
      },
    });

    ui.mount();
  },
});
```

## 検証観点

- buildが成功するか。
- `.output/{target}/manifest.json` が意図通りか。
- popupが開くか。
- content scriptが対象URLでだけ動くか。
- background listenerが動くか。
- permissionsやhost permissionsが最小か。
- ブラウザconsoleにentrypoint loaderやruntime APIのエラーがないか。

## 参考URL

- WXT Introduction: https://wxt.dev/guide/introduction
- WXT Installation: https://wxt.dev/guide/installation.html
- WXT Project Structure: https://wxt.dev/guide/essentials/project-structure.html
- WXT Entrypoints: https://wxt.dev/guide/essentials/entrypoints.html
- WXT Manifest: https://wxt.dev/guide/essentials/config/manifest
- WXT Content Scripts: https://wxt.dev/guide/essentials/content-scripts.html
- WXT Extension APIs: https://wxt.dev/guide/essentials/extension-apis
- WXT Storage: https://wxt.dev/guide/essentials/storage.html
- WXT Messaging: https://wxt.dev/guide/essentials/messaging
- WXT CLI: https://wxt.dev/api/cli/wxt
- 参考記事: https://zenn.dev/53able/articles/7e99295a28a75d
