# End-to-End (E2E) Testing Specification

> End-to-end testing guidelines for citizen report flows and municipal resolution.

---

# Scope

E2E tests validate complete user journeys across the application:
1. **Citizen Submission Flow**: Register/Login -> Capture Report -> GPS Geo-tag -> Submit -> View Status Updates.
2. **Department Resolution Flow**: Officer accepts assignment -> Updates status to `In Progress` -> Uploads completion evidence -> Resolves report.

---

# Tools & Frameworks

- **Mobile E2E**: Maestro / Detox for React Native user interaction simulation.
- **Backend/API E2E**: Python `pytest` suite running full docker-compose stack.

---

# Execution Schedule

- Run automatically on nightly builds and before staging/production deployment releases.
- Must execute against a fully configured local docker-compose environment with pre-seeded ward boundaries.
