# Agent Skills

## Purpose

Skills define reusable capabilities required by each role in AI Bug Fix Orchestrator.

A skill belongs to a **role or capability**, not to a specific AI provider. This keeps the workflow independent from Claude, Codex, Gemini, or any other provider.

## V1 Skills

### Shared — `project-context`

Used by Architect, Developer, and Reviewer.

Responsibilities:

- read configured project documentation;
- understand the relevant repository structure;
- identify files and modules related to the bug;
- respect documented architecture and project rules;
- avoid inventing constraints that are not documented or observable.

### Architect — `bugfix-planning`

Responsibilities:

- analyze the reported bug;
- identify the likely root cause;
- identify relevant files or components;
- produce a minimal implementation plan;
- document risks and architectural constraints;
- never modify source code.

Expected output: `FixPlan`.

### Developer — `safe-bugfix`

Responsibilities:

- follow the `FixPlan`;
- apply the smallest reasonable change;
- avoid unrelated refactoring;
- preserve existing architecture and contracts;
- run relevant tests when appropriate;
- keep changes visible through Git;
- produce an implementation summary.

Expected output: `ImplementationResult`.

### Reviewer — `diff-review`

Responsibilities:

- inspect `git diff`;
- compare the implementation with the original bug and plan;
- detect out-of-scope changes;
- check architectural compliance;
- identify obvious regression risks.

### Reviewer — `test-validation`

Responsibilities:

- discover the project's available test commands;
- prioritize tests related to changed code;
- run a broader suite when appropriate;
- record commands and results;
- report failing tests explicitly;
- never approve a fix when relevant tests fail.

Expected final output: `ReviewResult`.

## Suggested Permissions

| Role | Read files | Modify code | Inspect git diff | Run tests |
|---|---:|---:|---:|---:|
| Architect | Yes | No | Yes | Optional |
| Developer | Yes | Yes | Yes | Yes |
| Reviewer | Yes | No | Yes | Yes |

## Skill Layout

```text
skills/
├── shared/
│   └── project-context/
│       └── SKILL.md
├── architect/
│   └── bugfix-planning/
│       └── SKILL.md
├── developer/
│   └── safe-bugfix/
│       └── SKILL.md
└── reviewer/
    ├── diff-review/
    │   └── SKILL.md
    └── test-validation/
        └── SKILL.md
```

V1 intentionally starts with a small skill set. New skills should be added only when a real workflow requirement appears.
