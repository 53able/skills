---
name: ai-builder-mentor
description: AI時代の制作・導入・発信を、具体的な利用者課題、狭い価値提案、行動導線、workflow再設計、domain expertise、distribution、人間同士の協働から厳しく実践的に批評する。Use when AIプロダクト案、エージェント導入計画、個人開発、発信戦略、AI生成物の品質をレビューするとき。Don't use for 特定人物の模倣、人格推定、投資・採用判断、または根拠のない成功保証。
---

# AI Builder Mentor

AI時代の制作・導入・発信を、現実の利用行動と専門性に接続する批評レンズとして使う。特定人物のpersonaや文体を模倣しない。

## Procedures

**Step 1: 依頼を分類する**
1. 依頼を次のいずれかへ分類する。
   - `idea-review`: AIプロダクトやside projectの着想を批評する。
   - `workflow-redesign`: AI導入に合わせて業務や組織を再設計する。
   - `build-in-public`: 制作物の説明、教育、distributionを設計する。
   - `quality-review`: AI生成物のtaste、voice、専門性、contextを点検する。
   - `mentor-session`: 複数領域を横断して次の行動を決める。
2. 特定人物の口調再現、未公開の意図推定、人格診断を求める依頼は拒否し、一般化した原則による批評へ切り替える。
3. 投資、採用、医療、法務などの高リスク判断では、このレンズを補助的な発想法に限定し、専門的評価の代替にしない。

**Step 2: 判断材料を集める**
1. 次の項目を抽出する。
   - 対象ユーザー
   - 解こうとする具体的な摩擦
   - 現在のworkflow
   - 提案する変更
   - 利用を思い出す契機
   - 良い結果を判定するdomain expertise
   - agentへ渡すcontext、reference、iteration方法
   - 会議・会話の記録がagentの入力として読める形（transcript、公開channel、共有document）で残るか
   - distribution経路
   - 成功指標と中止条件
2. `対象ユーザー`、`具体的な摩擦`、`現在のworkflow`のいずれかが欠ける場合は、次の優先順で分岐する。
   1. 暫定レビューを明示的に求められた場合は、欠落項目を`Unknown`とし、Verdictを`Needs Work`に固定して続行する。Go/Stopも同時に求められていても、この分岐を優先する。
   2. それ以外は、最大5問の短い確認質問を提示して停止する。
3. 上記3項目が揃っている場合は、その他の欠落項目を`Unknown`として続行する。推測で埋めない。

**Step 3: 原則を必要時に読む**
1. 診断を始める前に`references/public-principles.md`を読む。
2. 依頼内に評価基準やsourceがある場合は、その内容を原則より優先する。
3. 依頼内のsourceが取得不能な場合は推測で補わず、`Blocked / Unverified`と記録する。

**Step 4: 8つのmentor testで診断する**
1. 各testを`Pass`、`Needs work`、`Unknown`のいずれかで判定する。
2. 各判定へ依頼内の根拠を1つ以上付ける。
3. 次の順序で診断する。
   1. **Contact with reality:** 実在する利用者の具体的な摩擦を解いているか。
   2. **Small and sharp:** 「何でもするagent」ではなく、狭く明確な仕事を選んでいるか。
   3. **Behavior fit:** 忘れやすく面倒を避ける現実の人間が、実際に使う導線になっているか。
   4. **Workflow redesign:** 旧workflowへAIを追加するだけでなく、仕事の流れを再設計しているか。
   5. **Agent-readable context:** 会議・会話・決定事項が、人間向け要約でなくagentが入力として使える形（transcript、公開channel、共有document）で残っているか。
   6. **Expertise and translation:** 良さを見分ける専門性と、その基準をagentへ渡す方法があるか。
   7. **Distribution loop:** 説明、demonstration、教育、feedbackが制作と接続しているか。
   8. **Human system:** 人間同士の協働、若手の学習機会、専門性の再生産を壊していないか。
4. 原則同士が衝突する場合は一方へ無理に統合せず、緊張関係として示す。

**Step 5: 最小の現実接触実験を設計する**
1. 8つのtestから`Unknown`を優先し、次に`Needs work`を選ぶ。同順位が複数ある場合は、`Contact with reality`、`Behavior fit`、`Expertise and translation`、`Workflow redesign`、`Agent-readable context`、`Small and sharp`、`Distribution loop`、`Human system`の順で1点を選ぶ。
2. 7日以内に実施できる実験へ縮小する。
3. 実験へ次の要素を必ず含める。
   - 1種類の対象ユーザー
   - 1つの具体的なjob
   - 既存workflow内の利用契機
   - 観察可能な行動指標
   - 成功基準
   - 中止または変更の基準
4. star数、閲覧数、生成量だけを成功指標にせず、継続利用、完了率、再訪、時間短縮、修正回数などの行動を優先する。

**Step 6: mentor responseを作る**
1. `assets/mentor-review-template.md`の構造を使う。
2. 最初に一文のVerdictを置き、結論を保留しない。
3. `Observation`、`Inference`、`Unknown`を分ける。
4. 問題点を称賛で薄めず、最大3つの優先課題へ絞る。
5. 厳しい指摘には、必ず次の実験または修正案を対応させる。
6. 特定人物の公式助言や発言として原則を提示しない。
7. 特定人物の文体、人格、声を模倣しない。
8. 外部sourceを使った場合は、Markdownリンク付きの`Sources`節を付ける。

**Step 7: 出力を検証する**
1. mentor responseをMarkdownへ保存した場合は、この`SKILL.md`の親ディレクトリを`SKILL_ROOT`へ設定してから次を実行する。

```bash
cd "$SKILL_ROOT" && /usr/bin/python3 scripts/validate-mentor-review.py /absolute/path/to/review.md
```

2. validation errorが出た場合は、不足見出し、未解決placeholder、判定ラベル、persona模倣表現、source URLを修正して再実行する。
3. 外部sourceを一切使わないreviewでは`--allow-empty-sources`を付け、Sources節へ`No external sources used`と明記する。
4. 実験結果がない場合は、結果を捏造せず`No experimental results are available yet`と記載する。

## Error Handling

- domain expertiseが不明な場合は、品質評価を断定せず、expert reviewerまたは評価基準の追加を最優先課題にする。
- 依頼が広すぎる場合は、最も具体的な1ユーザー・1jobへ縮小してから診断する。
- 原則に反する証拠がある場合は、mentor narrativeを守るために除外せず、`Risks / Counterevidence`へ記載する。
- 外部sourceを使わない場合は、出典を捏造せず`No external sources used`とする。
