# AI Bug Fix Orchestrator — Specification

## Purpose

AI Bug Fix Orchestrator is a local CLI tool that coordinates AI agents to analyze, implement, and review bug fixes in a software repository.

The project uses LangChain for workflow composition and follows Clean Architecture so that orchestration logic, agent roles, and AI providers remain decoupled.

The initial workflow has three configurable roles:

- **Architect** — understands the bug and project rules, then creates a safe implementation plan.
- **Developer** — follows the plan and applies the required code changes.
- **Reviewer** — reviews the resulting diff, validates the fix, and runs the available tests.

AI providers are replaceable. Claude, Codex, Gemini, or another compatible provider can be assigned to any role.

## V1 Scope

The first version should:

1. Receive a bug description from a local file or CLI input.
2. Read the project documentation and relevant repository context.
3. Run the workflow `Architect -> Developer -> Reviewer`.
4. Allow each role to use a configurable AI provider.
5. Operate on a local Git repository.
6. Keep code changes inspectable through Git.
7. Report the final review result in the terminal.

Out of scope for V1:

- HTTP API
- Web UI
- Database
- Queues
- Distributed execution
- Remote deployment

## Architecture

The project follows Clean Architecture with Ports and Adapters.

```text
CLI
 |
 v
Application / Workflow
 |
 v
LangChain
 |
 +--> ArchitectAgent
 +--> DeveloperAgent
 +--> ReviewerAgent
        |
        v
      Ports
        |
        v
     Adapters
 Claude / Codex / Gemini / others
```

### Layers

- **cli/** — receives user input and starts the use case.
- **application/** — contains workflows and orchestration logic.
- **ports/** — defines provider-independent contracts for agent roles.
- **adapters/** — integrates concrete AI providers and external tools.
- **domain/** — contains core models such as bug context, fix plan, implementation result, and review result.

The core rule is simple:

> Internal layers must depend on roles and contracts, not on specific AI providers.

The workflow should know about `ArchitectAgent`, `DeveloperAgent`, and `ReviewerAgent`, not directly about Claude, Codex, Gemini, or any other provider.

### Agent Configuration

Agent/provider selection, project documentation, and role skills live in
`config/agents.yaml`. Every role receives an `AgentContext` containing the
already-read documentation, shared skills, and its role-specific skills.

The application workflow depends on the role ports and the context-provider
port. Provider names such as `codex` are interpreted only by adapters and the
future composition root.

## Core Workflow

```text
Bug + Project Documentation
            |
            v
      ArchitectAgent
            |
            v
         FixPlan
            |
            v
      DeveloperAgent
            |
            v
  ImplementationResult
            |
            v
       ReviewerAgent
            |
            v
       ReviewResult
```

## Agent Responsibilities

### Architect

The Architect is responsible for understanding before changing.

It must:

- read the bug description;
- read the configured project documentation;
- inspect relevant code when necessary;
- identify the likely root cause;
- identify affected files or components;
- create a minimal implementation plan;
- highlight architectural constraints and risks;
- never modify source code.

Expected output: `FixPlan`.

### Developer

The Developer is responsible for implementation.

It must:

- read the bug context and the Architect's plan;
- follow the plan unless a blocking inconsistency is discovered;
- make the smallest reasonable change;
- avoid unrelated refactoring;
- preserve existing contracts and architecture;
- keep changes visible through `git diff`;
- provide a concise summary of the implementation.

Expected output: `ImplementationResult`.

### Reviewer

The Reviewer is responsible for independent validation.

It must:

- read the original bug and the Architect's plan;
- inspect the implementation and `git diff`;
- verify that the fix addresses the reported problem;
- detect unrelated or risky changes;
- check compliance with project architecture;
- run relevant tests;
- report failures clearly;
- not modify source code in V1.

Expected output: `ReviewResult`.

## Safety Principles

- Architect operates in read-only mode.
- Developer may write only inside the configured repository workspace.
- Reviewer operates in read-only mode but may run tests.
- Destructive commands must not run without explicit user permission.
- Every modification must remain reviewable through Git.
- A failed relevant test must never be hidden or reported as a successful review.

## V1 Success Criteria

A user should eventually be able to run a command similar to:

```bash
ai-bug-fix fix bug.md
```

and observe a workflow similar to:

```text
[architect] analyzing bug and project context
[architect] fix plan created
[developer] applying fix
[developer] implementation completed
[reviewer] reviewing diff
[reviewer] running tests
[reviewer] approved
```
