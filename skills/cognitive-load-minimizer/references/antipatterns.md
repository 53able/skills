# Cognitive Load Antipatterns

Use this reference when deciding whether a design choice creates extraneous cognitive load.

## Control Flow Load

- Complex conditionals: Boolean expressions that require remembering several partial truths.
  - Prefer named intermediate facts.
  - Keep the final branch readable as a business rule.
- Nested ifs: Deep indentation that forces readers to retain preconditions.
  - Prefer guard clauses when local style allows it.
  - Keep the main path visually dominant.

## Abstraction Load

- Inheritance chains: Behavior spread across parent and child classes.
  - Prefer composition when behavior varies independently.
  - Avoid edits that require reading every ancestor and descendant first.
- Shallow modules: Many tiny methods, classes, or files whose interfaces exceed their value.
  - Prefer deep modules with simple interfaces.
  - Keep important crux logic visible enough to find.
- SRP misread as "one tiny thing": Factories, wrappers, and helpers whose names carry more complexity than their implementation.
  - Judge responsibility by stakeholder and change reason, not by line count.

## Distributed Load

- Shallow microservices: Services that change together, deploy together, or require local reproduction together.
  - Prefer modular monoliths until separate deployment, scaling, or ownership is real.
  - Delay network boundaries until the team has enough domain information.
- Distributed monoliths: Network calls that preserve tight coupling while adding debugging cost.
  - Reduce cross-service change paths before adding more service boundaries.

## Language And Framework Load

- Feature-rich language tricks: Syntax that requires remembering specification details.
  - Prefer idioms that the local team reads without reconstructing a standards discussion.
- Framework magic in core logic: Business rules hidden behind lifecycle hooks, decorators, implicit naming, or generated behavior.
  - Keep framework integration at the edges.
  - Test core behavior without booting framework infrastructure where possible.

## Protocol And Mapping Load

- Business meaning encoded in numeric status values.
  - Use self-describing domain codes in payloads.
  - Reserve transport status for broad transport semantics.
- Custom enum or database codes without nearby names.
  - Prefer named constants, schemas, or explicit dictionaries close to the boundary.

## Architecture Load

- DRY abuse: Shared helpers created before concepts prove identical.
  - Keep a little duplication when abstraction would couple unrelated features.
  - Extract after observing repeated change in the same direction.
- Decorative layers: Ports, adapters, repositories, services, or folders added to satisfy an architecture image.
  - Add layers only when they hide real complexity or protect a practical extension point.
- DDD as folder structure: Domain terms used as ceremony rather than shared language.
  - Keep DDD focused on problem-space understanding, boundaries, and stakeholder language.

## Familiarity Trap

- Familiar code that feels simple only because long-term maintainers memorized it.
  - Ask a newer contributor to trace the change path.
  - Treat confusion beyond roughly 40 minutes as a signal to improve structure or documentation.
