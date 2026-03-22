# Agent Skills

A collection of agent skills for structured thinking, multi-perspective analysis, and development workflows.

## Thinking & Analysis

Skills that apply structured cognitive frameworks to decisions and problem-solving.

- **thinking-ensemble** — 16 MBTI cognitive lenses across 4 parallel agent groups (NT/NF/SJ/SP). Maximizes perspective diversity by running all 4 groups simultaneously as sub-agents and synthesizing with task-weighted integration.

```
npx skills@latest add oreore/skills/thinking-ensemble
```

## Install

```bash
# Install individual skills
npx skills@latest add oreore/skills/<skill-name>
```

## Skill Structure

Each skill lives in its own directory:

```
<skill-name>/
├── SKILL.md          # Main skill definition (loaded by Cursor)
└── *.md              # Supporting files bundled with the skill
```

Skills are designed for [Cursor](https://cursor.com) and follow the Agent Skills format.
