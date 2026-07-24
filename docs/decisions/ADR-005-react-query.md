# ADR-005: Selection of React Query (TanStack Query) for Mobile Server State

- **Status**: Accepted
- **Date**: 2026-07-23
- **Deciders**: Mobile Team

---

# Context

The React Native mobile app frequently fetches, caches, updates, and synchronizes report lists, user profiles, and notification feeds with the FastAPI backend. Managing loading states, cache invalidation, and background refetching manually creates buggy and repetitive code.

# Considered Options

1. **Zustand / Redux Manual Fetching**: Requires storing raw API payloads in global stores and writing manual loading/error state management for every endpoint.
2. **RTK Query**: Tied to Redux ecosystem, adding boilerplate to a lightweight React Native setup.
3. **TanStack React Query v5**: Purpose-built server state management library providing declarative queries, automatic caching, garbage collection, and optimistic UI updates.

# Decision

We selected **TanStack React Query v5** for mobile server state management.

# Rationale

- **Declarative Data Fetching**: Simplifies component code with `useQuery` and `useMutation` hooks.
- **Smart Caching & Deduplication**: Prevents redundant network requests across navigation tabs.
- **Optimistic Updates**: Immediate UI feedback for report submission and profile updates before server confirmation.
- **Integration with Zustand**: Clear separation between client UI state (Zustand) and server cache (React Query).

# Consequences

- **Positive**: Clean component code, fast UI responses, built-in retry and caching mechanisms.
- **Negative**: Developers must understand React Query cache key hierarchies and invalidation patterns.
