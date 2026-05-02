# Cognitive Load Review Checklist

Use this checklist before recommending or accepting a cognitive-load reduction.

## Task Fit

- [ ] The task boundary is clear.
- [ ] The affected reader persona is named.
- [ ] Intrinsic domain complexity is not being disguised as removable complexity.
- [ ] Existing project style and public contracts are preserved unless the task explicitly changes them.

## Control Flow

- [ ] Complex conditions use named intermediate facts or small predicates.
- [ ] Guard clauses remove nesting where behavior remains obvious.
- [ ] The happy path is visible without retaining several preconditions in memory.
- [ ] Error paths do not obscure the main path.

## Module Shape

- [ ] Modules hide meaningful complexity behind simple interfaces.
- [ ] Shallow wrappers, pass-through helpers, and tiny ceremony files are justified.
- [ ] Important crux logic is findable.
- [ ] Related behavior is not scattered across many files solely to satisfy line-count rules.

## Coupling

- [ ] Shared abstractions represent stable sameness, not temporary resemblance.
- [ ] Duplication is removed only when removal lowers total change cost.
- [ ] Framework details stay outside core business logic where practical.
- [ ] Service boundaries match deployment, scaling, ownership, or failure isolation needs.

## Protocols And Names

- [ ] Domain outcomes use self-describing names.
- [ ] Numeric transport codes are not overloaded with product-specific meaning.
- [ ] Custom mappings are centralized and close to the boundary.
- [ ] Domain terms match stakeholder language.

## Verification

- [ ] The simplification reduces file jumps, call-stack jumps, or mental mappings.
- [ ] Behavior preservation is verified by tests or a concrete manual check.
- [ ] The change does not move complexity into hidden magic.
- [ ] Review comments cite observable maintenance or onboarding cost, not taste.
