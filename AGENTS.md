# AGENTS.md

# CivicConnect Agentic Operational Contract

This document provides system guidelines for agentic assistants and Claude Code working on CivicConnect.

## Default Automatic Workflow

When given any feature or task request (e.g. *"implement login auth"*), the assistant MUST automatically execute:

1. **Research & Audit**: Read `docs/specs/` and `docs/architecture/` first to find what to build, why, and evaluate the best approach.
2. **Task Planning**: Create execution plans in `docs/plans/<task>.md` prior to code generation.
3. **Layer Separation**: Enforce `API Routes -> Service Layer -> Database Models`. Never mix HTTP handler logic with SQL queries.
4. **Zero-Hallucination Implementation**: Use explicit typing and ground truth schema contracts from `docs/specs/`.
5. **Quality Verification**: Execute `mypy --strict`, `ruff check`, ESLint, TypeScript checks, and tests before concluding.
6. **Auditability**: Every AI pipeline action must generate immutable audit records in `agent_executions`.
