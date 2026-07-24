# Code Review Guidelines

> Guidelines and checklists for code reviews in CivicConnect.

---

# Code Review Objectives

1. Maintain system security, reliability, and data privacy.
2. Ensure strict adherence to project specifications in `docs/specs/` and `docs/architecture/`.
3. Verify test coverage and static analysis compliance before merging code into `develop` or `main`.

---

# Reviewer Checklist

## 1. Architecture & Design
- Does the implementation conform to approved architecture and ADR decisions?
- Is layer separation preserved (Route -> Service -> Model)?

## 2. Quality & Typing
- Do all Ruff, MyPy, ESLint, and TypeScript checks pass?
- Are functions cleanly typed without `any` or untyped parameters?

## 3. Testing & Coverage
- Are unit tests included for new functions/modules?
- Are edge cases and error paths tested?

## 4. Security & Privacy
- Are credentials, API keys, or JWT tokens absent from code and logs?
- Is input properly validated via Pydantic or Zod schemas?
