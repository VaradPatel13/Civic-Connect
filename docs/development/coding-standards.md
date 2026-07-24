# Coding Standards

> Code quality, formatting, typing, and linting standards for CivicConnect.

---

# Python Standards (Backend & Scripts)

- **Version**: Python 3.12+
- **Formatter & Linter**: `ruff`
- **Type Checker**: `mypy` (Strict Mode)

## Rules
- All functions must include explicit type hints for parameters and return values.
- Async I/O used for all database, network, and disk calls.
- Use Pydantic v2 schemas for request validation and response serialization.
- Follow PEP 8 variable and module naming conventions (snake_case).

---

# TypeScript & React Native Standards (Mobile)

- **Version**: TypeScript 5.0+ (Strict Mode)
- **Linter & Formatter**: ESLint + Prettier

## Rules
- No `any` types permitted. Define explicit TypeScript interfaces/types.
- All visual components must support light/dark modes and multi-language strings via `i18next`.
- React hooks must follow standard rules of hooks and specify explicit dependency arrays.
