# AI Builder Mentor Principles

## 使用上の境界

- 以下はAI時代の制作・導入・発信を評価するために一般化した批評レンズである。
- 特定人物の性格、私的動機、未公開の意図を推定しない。
- 自己報告、仮説、外部検証済みの事実を区別する。
- 原則同士の緊張を消さず、用途と文脈に応じて使い分ける。

## Principle 1: AIを旧workflowへ足すだけで終わらせない

AI導入の価値は、既存工程を少し速くすることではなく、仕事の流れ、役割、handoff、管理方法を再設計できるかで判断する。

**Mentor questions**

- AIを外した場合と同じ工程や組織図を維持していないか。
- agentが処理できる単位まで仕事を分解したか。
- 人間の承認が必要な境界は明確か。

## Principle 2: Big and genericではなくsmall and sharpを選ぶ

「仕事と生活のすべてを行うagent」のような広い約束を避け、対象ユーザー、job、評価基準が明確な小さい楔を選ぶ。既存の汎用agentと比較して、固有のopinionを説明できない案は弱い。

**Mentor questions**

- 誰の、どの瞬間の、何を終わらせるのか。
- 既存の汎用agentだけでは足りない理由は何か。
- 非対象ユーザーを明言できるか。
- そのskillや手順は、実作業を繰り返した末に抽出したものか、それとも一度も実行せずに書いた仕様か。後者の場合、想定と実際の摩擦がずれるリスクを織り込んでいるか。

## Principle 3: 動くかではなく、実際に使うかを検証する

実装完了を成功としない。利用者は忘れ、面倒を避け、理想どおりの手順を踏まない。新しいappを開かせる負担を避け、feed、calendar、document、communication surfaceなど、すでに見る場所へ利用契機を埋め込む。

**Mentor questions**

- 利用者は何をきっかけに思い出すのか。
- 新しいdashboardを開く必要があるか。
- 1週間後も自発的に使ったか。

## Principle 4: Tasteを持たずにAIへ品質を委ねない

AI生成自体を問題にせず、良い結果を見分けるtaste、voice、domain expertiseがあるかを問う。専門性と、専門性をcontext・reference・iterationへ変換するtranslation skillを分ける。

**Mentor questions**

- 良い結果の具体例と悪い結果の具体例はあるか。
- 誰が最終品質を判定できるか。
- 判断基準をagentへ再利用可能な形で渡したか。
- 出力は固有の経験や一次情報に支えられているか。

## Principle 5: Buildingとdistributionを同じloopで設計する

制作後に宣伝を追加するのではなく、説明、demonstration、教育、feedbackを制作へ接続する。feature logの量産ではなく、問題、判断、失敗、学び、改善過程を具体的に示す。

**Mentor questions**

- 見せるdemoはあるか。
- 利用者が学べる説明になっているか。
- 公開後に何を観察し、何を変えるのか。
- builder本人の具体的な判断が見えるか。

## Principle 6: 抽象研修よりmeaningful taskを完了させる

AI研修を講義だけで終えず、利用環境のsetupと本人の実務task完了までを一つの導入単位にする。install、permission、credential、data accessなどのsetup frictionを軽視しない。

**Mentor questions**

- 研修中に実タスクを完了できるか。
- setupの障壁を除いたか。
- 参加者同士が学びを共有できるか。

## Principle 7: Human-agentだけでなくhuman-human-agentを設計する

個人とagentの生産性だけを最大化すると、人間同士の会話、共同判断、team cultureが弱まる場合がある。agentを協働の代替ではなく、協働へ組み込む。

**Mentor questions**

- agent利用後も、人間同士が判断を共有する接点は残るか。
- agentの出力や失敗からteam全体が学べるか。
- single-player productivityがteam outcomeを悪化させていないか。

## Principle 8: 専門性を消費するだけでなく再生産する

AI出力の監督にはexpertiseが必要だが、expertiseは初級業務や反復経験から育つ。junior workを除去する場合は、次世代のexpertを育てる別のlearning loopを設計する。

**Mentor questions**

- 誰がAIの誤りを見抜くのか。
- 初学者は何を通じて判断力を獲得するのか。
- automation後も、失敗例と修正理由へ接触できるか。

## Principle 9: 情報をagentが読める形で残す

会話、会議、意思決定は人間が読み返すためだけでなく、agentが入力として使える形（transcript、公開channel、共有document）で残っているかを問う。private chatや口頭のみに情報が閉じていると、agentは会社やprojectの文脈を扱えない。

**Mentor questions**

- 会議やチャットの記録は、agentが後で読める形（transcript、公開channel、共有document）で残るか。
- 決定事項は公開channelや共有documentにあるか、それとも個人のDMや記憶に閉じているか。
- 会話記録を実装コンテキスト（例: meeting transcriptをPRD代わりに使う）として使う場合、要件の揺れ、機密情報、レビュー不足、誤実装のリスクをどう扱うか。

## Counterweights

- 小規模teamと会議削減は常に正しいわけではない。human-human-agentの原則と同時に評価する。
- hands-on learningを重視しても、書籍、講演、formal educationの価値を一律に否定しない。
- distributionを重視しても、viewsやfollowersをproduct valueの代理指標にしない。
- coding accessibilityが上がっても、domain expertiseが不要になったとは解釈しない。
- 会話をagentが読める形で記録・共有することと、人間同士の会話や会議そのものを減らすことは同義ではない。前者を勧めても、Principle 7の懸念（human-human接点の消失）を打ち消さない。
