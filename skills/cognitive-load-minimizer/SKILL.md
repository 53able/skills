---
name: cognitive-load-minimizer
description: Reduces extraneous cognitive load in code reviews, refactors, architecture decisions, and feature implementation by identifying avoidable mental overhead, shallow abstractions, clever conditionals, premature layers, framework coupling, and misleading domain models. Use when simplifying code, reviewing design, onboarding contributors, or evaluating maintainability. Do not use for performance tuning, UI copy editing, or domain complexity that cannot be reduced.
---

# Cognitive Load Minimizer

Reduce avoidable mental overhead in software. Preserve intrinsic domain complexity; remove presentation, structure, and architecture choices that force future contributors to rebuild unnecessary mental models.

## Procedures

**Step 1: Establish The Task Boundary**
1. Identify the change type: code review, refactor, feature implementation, architecture decision, or onboarding improvement.
2. Name the reader persona: new contributor, adjacent team member, future maintainer, QA engineer, or current feature owner.
3. Separate intrinsic complexity from extraneous complexity:
   - Intrinsic: domain rules, correctness requirements, real scalability constraints, data model facts.
   - Extraneous: clever expression, needless indirection, shallow decomposition, custom mappings, framework magic, subjective architecture vocabulary.
4. If the confusion comes from missing domain knowledge rather than code structure, document the domain fact instead of reshaping the code.

**Step 2: Scan For Load Sources**
1. Read `references/antipatterns.md` when the task involves architectural or refactoring judgement.
2. Run `python scripts/score-cognitive-load.py --path <file-or-directory>` when a quick heuristic scan of code text is useful.
3. Treat script output as a triage aid only. Verify every finding by reading the surrounding code.
4. Mark each finding with one category:
   - Control flow load
   - Abstraction load
   - Coupling load
   - Protocol or mapping load
   - Framework or language load
   - Onboarding load

**Step 3: Prefer Low-Load Transformations**
1. Replace complex conditionals with named intermediate facts.
2. Replace nested happy paths with guard clauses when that preserves behavior and local style.
3. Prefer composition and explicit collaboration over inheritance chains that require reading parent classes before editing.
4. Merge or inline shallow modules when their interface is harder to understand than their implementation.
5. Delay abstractions until a stable variation point exists. Keep small duplication when removing it would couple unrelated concepts.
6. Keep core business logic independent from framework entry points. Use framework objects at the edges.
7. Use self-describing domain codes instead of forcing contributors to remember numeric or transport-level mappings.
8. Add architecture layers only when they hide real complexity or protect a practical extension point.
9. Keep DDD, Clean Architecture, and pattern names subordinate to the actual domain language and change paths.

**Step 4: Validate The Simplification**
1. Read `references/checklist.md` and evaluate the candidate change.
2. Confirm behavior preservation with existing tests, focused new tests, or an explicit manual verification plan.
3. Check whether the new structure reduces required jumps across files, stacks, services, or mental mappings.
4. Check whether a new contributor can identify the main path before reading edge cases.
5. Reject simplifications that only move complexity somewhere else.

**Step 5: Report Findings**
1. Use `assets/review-template.md` for review comments or design notes.
2. Lead with the specific cognitive load source, then state the smaller replacement.
3. Avoid taste-based language. Ground each recommendation in changed files, runtime behavior, onboarding cost, or debugging path length.
4. If no low-risk reduction exists, say that the complexity appears intrinsic and name the evidence.

## Error Handling

* If the heuristic script reports many low-confidence findings, narrow the scan to the files touched by the task.
* If a proposed simplification changes public behavior, stop and require tests or explicit product approval.
* If local project conventions conflict with this skill, preserve shipped public interfaces and reduce load inside the nearest safe boundary.
* If an abstraction looks shallow but is part of a stable public API, prefer documentation or examples over removal.
