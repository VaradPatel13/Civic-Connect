# Execution Plan: Login & Registration Authentication APIs

## Objective
Implement zero-hallucination, secure, production-ready Authentication APIs (`/api/v1/auth/*`) in FastAPI following the layer separation contract (`API Routes -> Service Layer -> Repository Layer -> Database Models`) as specified in `docs/specs/auth.md` and `docs/specs/users.md`.

---

## 1. Research & Audit Summary
- **Database Schema**: `citizens`, `sessions`, and `otp_codes` tables are already created and migrated (Alembic revision `dd3c5874a143`).
- **Layers Needed**:
  - `backend/schemas/auth.py`: Pydantic v2 schemas for requests & responses.
  - `backend/repositories/user.py`: Async SQLAlchemy 2.x queries for `Citizen`, `Session`, and `OTPCode`.
  - `backend/services/auth_service.py`: Business logic for registration, password verification, OTP handling, JWT issuance/verification, token rotation, and logout.
  - `backend/api/deps.py`: Auth dependency (`get_current_user`) enforcing Bearer JWT token verification.
  - `backend/api/auth.py`: FastAPI route handlers for `/auth/register`, `/auth/verify-otp`, `/auth/login`, `/auth/refresh`, `/auth/logout`, and `/auth/me`.
  - `backend/main.py`: CORS middleware and router mounting under `/api/v1`.

---

## 2. Plan of Action

### Step 1: Update Schemas (`backend/schemas/auth.py`)
- Define `RegisterRequest`: `display_name`, `phone`, `password`, optional `email`, `preferred_language` (`en`, `hi`, `mr`).
- Define `LoginRequest`: `phone`, `password`.
- Define `OTPVerifyRequest`: `phone`, `code`, `purpose`.
- Define `RefreshRequest`: `refresh_token`.
- Define `CitizenProfileResponse`: PII-safe citizen object (`id`, `display_name`, `phone`, `email`, `preferred_language`, `points`, `is_verified`, `role`, `created_at`).
- Define `AuthSuccessResponse`: `access_token`, `refresh_token`, `token_type`, `expires_in`, `user`.

### Step 2: Refine Repository Layer (`backend/repositories/user.py`)
- Add `get_by_id(user_id: UUID)`.
- Fix `revoke_session` with explicit `func.now()`.
- Add `revoke_all_sessions(citizen_id: UUID)`.

### Step 3: Enhance Service Layer (`backend/services/auth_service.py`)
- Implement password hashing (`pwd_context.hash` / `verify`).
- Implement JWT access token (15 mins) & refresh token (7 days) creation with sub, role, and exp claims.
- Implement token refresh logic with session token hash validation.
- Implement OTP verification logic (expiration, retry counts, consumption).

### Step 4: Auth Dependency (`backend/api/deps.py`)
- Create `get_current_user` using FastAPI `HTTPBearer` security scheme.
- Decode JWT token, verify expiration, look up citizen by ID in `UserRepository`.

### Step 5: Implement API Routes (`backend/api/auth.py`)
- `POST /auth/register` -> Create unverified citizen & generate OTP.
- `POST /auth/verify-otp` -> Verify OTP, mark account as verified, issue tokens & session.
- `POST /auth/login` -> Verify credentials, issue tokens & session.
- `POST /auth/refresh` -> Validate refresh token, revoke old session, issue new token pair.
- `POST /auth/logout` -> Revoke active session.
- `GET /auth/me` -> Return current authenticated profile.

### Step 6: Mount Router & CORS in `backend/main.py`
- Add `CORSMiddleware`.
- Include `auth.router` under `/api/v1`.

### Step 7: Tests & Verification
- Write unit/integration tests in `tests/integration/test_auth_api.py`.
- Run tests with `pytest`.
- Execute static quality verification.

---

## 3. Definition of Done
- [ ] All 6 authentication endpoints functional and mounted at `/api/v1/auth/`.
- [ ] Clean layered separation (Routes -> Service -> Repository -> Models).
- [ ] CORS middleware configured for web and Expo clients.
- [ ] Integration tests pass with `pytest`.
