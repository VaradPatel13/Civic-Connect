# Session Persistence & Dashboard Designer Refactor Implementation Plan

## Goal
1. Maintain logged-in user sessions for >30 days (up to 60 days) on both backend JWT configuration and mobile app Zustand persistent storage.
2. Refactor the `app/app/(tabs)/index.tsx` page to a high-end designer, Gen-Z styled, dark glassmorphism aesthetic with micro-animations and zero generic AI boilerplate appearance.

## Architectural Changes

### 1. Backend JWT & Session Expiration (`backend/core/config.py` & `backend/services/auth_service.py`)
- Update `access_token_expire_minutes` from `15` to `43200` (30 days) or `86400` (60 days).
- Update `refresh_token_expire_days` from `7` to `60` days.
- Ensure token issue and expiration timestamps properly honor extended session lifespans.

### 2. Frontend Auth Session Storage (`app/src/store/useAuthStore.ts` & `app/src/lib/api.ts`)
- Implement persistent storage so JWT tokens and citizen profile sessions survive app restarts and reloads for >30 days.
- Ensure `fetchCurrentUser()` handles silent session re-validation gracefully without logging out active users on transient network glitches.

### 3. Designer UI Refactor (`app/app/(tabs)/index.tsx`)
- Polish the dark glassmorphic UI with vibrant neon accents (`#A855F7`, `#3B82F6`, `#34D399`, `#FB7185`).
- Ensure bento grid metrics, live pulses, micro-interactions, responsive typography, and customized interactive chips feel ultra-premium.

## Verification
1. Run `python -m pytest` to ensure auth token creation & verification tests pass.
2. Run `npx tsc --noEmit` in `app/` to ensure zero TypeScript errors.
