---
name: chuuni-refiner
description: Refines Japanese prose into a requested 厨二 level by adding controlled dark-fantasy grandiosity, special-existence framing, dramatic naming, and over-the-top self-seriousness while preserving intent. Use when transforming drafts, character lines, skill names, game text, slogans, or prompts into low, medium, high, or max 厨二 style. Don't use for factual reports, legal text, medical advice, formal business writing, or cases where naturalness, accessibility, or citation fidelity matters more than stylization.
---

# 厨二 Refiner

Transform Japanese text into a chosen 厨二 level while preserving the user's core meaning, constraints, and requested format.

## Workflow

1. **Extract the request.** Identify the source text, target audience, output format, and desired 厨二 level.
2. **Infer the level if omitted.** Use `medium` for general requests like「厨二っぽくして」. Use `max` only when the user asks for「全開」「MAX」「限界」「盛って」.
3. **Load the definition when needed.** Read `references/chuuni-definition.md` when the task asks what 厨二 means, when calibrating level, or when resolving borderline tone.
4. **Get level knobs.** Run `python3 scripts/level-guide.py --level <low|medium|high|max>` to obtain the permitted intensity profile.
5. **Preserve intent.** Keep factual content, names, relationships, required terms, length limits, and user-provided structure unless the user asks for free adaptation.
6. **Refine the text.** Add only the amount of dark-fantasy grandiosity, special-existence framing, dramatic diction, symbolic nouns, and self-serious rhythm allowed by the selected level.
7. **Avoid unsupported facts.** Do not add real-world claims, citations, technical claims, credentials, prices, dates, or measurable results unless present in the source text.
8. **Check harm and context.** Avoid turning personal insults, harassment, legal/medical advice, or factual reports into manipulative or misleading stylized text. Offer a safer creative version when needed.
9. **Return the result.** Provide the refined text first. Add a short note only when level, preservation, or safety constraints materially changed the output.

## Level calibration

Use these defaults unless `scripts/level-guide.py` gives more specific guidance:

- `low`: Slightly dramatic. Keep natural Japanese. Add one or two sharper words.
- `medium`: Clearly 厨二. Add fate, shadow, awakening, oath, forbidden, or sealed-force motifs sparingly.
- `high`: Strong 厨二. Use ornate compounds, dramatic pauses, worldline/fracture/contract imagery, and heightened self-seriousness.
- `max`: Deliberately excessive. Use grand names, sealed powers, apocalypse-scale metaphors, archaic rhythm, and theatrical declarations while keeping the base meaning recognizable.

## Transformation rules

1. **Name the hidden force.** Convert plain motivation into an inner flame, sealed will, oath, fragment, resonance, or forbidden protocol.
2. **Raise stakes metaphorically.** Turn ordinary difficulty into trial, covenant, threshold, rupture, fate, or abyss without inventing concrete events.
3. **Sharpen rhythm.** Use short declarations, controlled pauses, and sentence-final force. Avoid endless ornament.
4. **Choose motifs consistently.** Pick one motif family per output: darkness, stars, seals, ancient contract, forbidden archive, blade, divine/fallen, or machine-magic.
5. **Keep readability.** Preserve the user's communicative goal. If the result becomes unreadable, lower one intensity step.
6. **Respect genre.** For game text, prioritize names and battle cries. For essays, add subtle metaphors. For slogans, keep punch and brevity. For dialogue, preserve speaker personality.

## Output patterns

- For a single sentence: return one refined sentence.
- For alternatives: return 3 variants labeled by level or mood.
- For long text: return the rewritten text, then a compact change note.
- For naming requests: return candidates with kana/romaji only when requested.

## Error Handling

- If no source text is provided, ask for the text to refine and the desired level.
- If the requested level is ambiguous, choose `medium` and state the assumption in one line.
- If the text must remain factual or formal, refuse excessive stylization and offer `low` level only.
- If `scripts/level-guide.py` fails, use the Level calibration section and mention that script validation was unavailable.
- If the user requests abusive targeting, transform the output into fictional self-directed or non-targeted dramatic wording.
