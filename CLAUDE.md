# CLAUDE.md

# CivicConnect — Autonomous Development & Zero-Hallucination Agentic Operating Contract

> This document defines the full operating system, system prompts, research workflows, coding standards, design aesthetics, and execution guidelines for **Claude Code**.
>
> **DEFAULT BEHAVIOR**: Whenever the user gives a short request (e.g., *"implement login auth"* or *"build report tracking"*), Claude Code MUST AUTOMATICALLY execute the 4-phase **Research → Evaluate → Plan → Implement & Verify** workflow described below without needing to be asked.

---

# 1. Automatic 4-Phase Execution Workflow (DEFAULT FOR ALL REQUESTS)

Whenever given any feature, bug, or implementation prompt, Claude Code MUST execute these 4 phases sequentially:

```
PHASE 1: Research & Options Audit
   ├── Search & read docs/specs/ and docs/architecture/
   ├── Audit existing codebase modules for reusable patterns
   └── Identify options: Compare what to build, why, best library/approach, pros/cons
           │
           ▼
PHASE 2: Plan Generation
   └── Create/update `docs/plans/<task>.md` with architecture, schemas, affected files, risks
           │
           ▼
PHASE 3: Zero-Hallucination Implementation
   ├── Follow layer separation (Route -> Service -> Model)
   └── Use ONLY verified imports, existing contracts, and explicit Pydantic/TypeScript types
           │
           ▼
PHASE 4: Verification & Quality Gates
   ├── Run `ruff check`, `mypy --strict`, `pytest` (Backend)
   ├── Run `eslint`, `tsc --noEmit`, `jest` (Mobile)
   └── Fix any static analysis or test failures before completing
```

---

# 2. Tool Capabilities & System Directives

### A. Research & Zero-Hallucination Rules
- **Ground Truth Only**: Always base implementations on specifications in `docs/specs/` (`auth.md`, `reports.md`, `users.md`, `departments.md`, `ai-pipeline.md`, `database.md`, `api.md`). Never invent non-existent API parameters or library methods.
- **Web & Documentation Search**: If a library or external dependency API is uncertain, perform a search/doc lookup before writing code.
- **Explain Tradeoffs**: When choosing between multiple design patterns or libraries, explain *why* the chosen option is best suited for CivicConnect.

### B. Terminal & Process Execution
- **Non-Blocking Background Tasks**: When running dev servers or background workers (`uvicorn`, `expo start`, `celery`), use background execution and monitor status.
- **Command Verification**: Always verify exit codes and output lines after executing `pytest`, `mypy`, `ruff`, or `npm test`.

### C. Code & File Operations
- **Preserve Documentation**: Maintain existing docstrings, comments, and annotations.
- **Minimal Edits**: Make targeted replacements instead of replacing full files unnecessarily.

---

# 3. Web & UI Design Aesthetics (Mobile & Web)

When building or modifying user interfaces (React Native / Web):

1. **Rich Aesthetics**: High visual impact. Use curated HSL palettes (dark mode, modern municipal color tokens, subtle glassmorphism), dynamic gradients, and refined shadows.
2. **Modern Typography**: Use modern font families (Inter, Roboto, Outfit) instead of default system fonts.
3. **Micro-Animations & Dynamic States**: Add smooth hover states, touch feedback, loading skeletons, and subtle transition animations (`react-native-reanimated`).
4. **No Placeholders**: Never use generic placeholder boxes or text. Generate or define realistic mock data and SVG/Cloudinary media assets.

---

# 4. Architectural Contracts

### Priority Order (Source of Truth)
1. Explicit user prompt instructions
2. Approved specifications in `docs/specs/`
3. Architecture documentation in `docs/architecture/`
4. Architecture Decision Records in `docs/decisions/` (`ADR-001` to `ADR-005`)
5. This `CLAUDE.md` file

### Layered Separation
```
FastAPI Route Handler (api/)  --> Input Validation & Auth Dependency
        │
        ▼
Service Layer (services/)      --> Pure Business Logic (No HTTP/FastAPI types)
        │
        ▼
Data Repository Layer (models/)--> Async SQLAlchemy Queries & Models
```

---

# 5. Technology Stack & Coding Standards

### Backend (Python 3.12+)
- **Framework**: FastAPI + Pydantic v2
- **ORM**: Async SQLAlchemy 2.x + `asyncpg` driver + PostGIS (`GeoAlchemy2`)
- **Background Tasks**: Celery + Redis
- **AI Framework**: LangGraph + LangChain + NVIDIA NIM / OpenRouter
- **Static Analysis**: `ruff check` (linting), `mypy --strict` (type checking)

### Mobile (React Native + Expo)
- **Framework**: Expo (Managed Workflow) with `expo-router`
- **Server State**: TanStack React Query v5
- **Client State**: Zustand (persisted to MMKV)
- **Localization**: `i18next` (English `en`, Hindi `hi`, Marathi `mr`)
- **Quality**: TypeScript strict mode (`noImplicitAny: true`, ESLint clean, Prettier formatted)

---

# 6. Definition of Done & Quality Gates

A task is complete ONLY when all the following conditions are met:

- [ ] Automatic 4-phase workflow executed (Research → Plan → Code → Verify)
- [ ] Task plan created/updated in `docs/plans/`
- [ ] `mypy` strict type checking passes with 0 errors
- [ ] `ruff` linting and formatting pass cleanly
- [ ] Unit & integration tests written and passing (`pytest` / `jest`)
- [ ] Relevant documentation updated under `docs/`
- [ ] Self-review conducted: no dead code, no unhandled exceptions, no secret leaks

---

# 7. Git & Commit Guidelines

Use **Conventional Commits**:
- `feat: <description>` for new capabilities
- `fix: <description>` for bug fixes
- `docs: <description>` for documentation updates
- `refactor: <description>` for non-functional code improvements
- `test: <description>` for adding or updating test suites
- `chore: <description>` for dependency updates and environment configuration