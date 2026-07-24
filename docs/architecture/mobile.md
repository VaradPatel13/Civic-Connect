# Mobile Architecture

> This document describes the architectural design of the CivicConnect mobile application.
>
> It is the authoritative reference for the React Native application structure, navigation, state management, offline handling, and data flow patterns.

---

# Overview

The CivicConnect mobile application is built with React Native and Expo, targeting Android and iOS. It provides citizens with the ability to report civic issues, track resolution status, and receive real-time notifications.

All communication with external services passes through the FastAPI backend. The mobile app never contacts Cloudinary, NVIDIA NIM, or Firebase directly.

---

# Technology Stack

| Component | Technology |
|-----------|-----------|
| Framework | React Native (Expo managed workflow) |
| Routing | expo-router (file-based) |
| Server state | TanStack React Query v5 |
| Client state | Zustand |
| Localization | i18next + react-i18next |
| Maps | MapLibre GL via WebView |
| Offline storage | MMKV |
| Network detection | @react-native-community/netinfo |
| Image picker | expo-image-picker |
| Location | expo-location |
| Push notifications | expo-notifications + FCM |
| HTTP client | axios with interceptors |
| Form handling | react-hook-form + zod |
| Animations | react-native-reanimated |

---

# Repository Structure

```
app/
├── (auth)/                     # Unauthenticated screens
│   ├── _layout.tsx
│   ├── login.tsx
│   ├── register.tsx
│   ├── verify-otp.tsx
│   └── forgot-password.tsx
│
├── (tabs)/                     # Main authenticated tab navigator
│   ├── _layout.tsx
│   ├── index.tsx               # Home dashboard
│   ├── reports.tsx             # My reports list
│   ├── new-report.tsx          # Report submission
│   ├── notifications.tsx       # Notifications
│   └── profile.tsx             # Profile and settings
│
├── report/
│   └── [id].tsx                # Report detail
│
└── _layout.tsx                 # Root layout with auth guard
│
components/
├── ui/                         # Generic UI primitives
├── reports/                    # Report-specific components
├── auth/                       # Auth components
└── notifications/
│
hooks/
├── useAuth.ts
├── useReports.ts
├── useLocation.ts
├── useOfflineQueue.ts
├── useNotifications.ts
└── useNetworkStatus.ts
│
stores/
├── authStore.ts                # JWT tokens, citizen identity
├── offlineStore.ts             # Offline report queue
└── settingsStore.ts            # User preferences
│
services/
├── api.ts                      # axios instance with interceptors
├── authService.ts
├── reportService.ts
└── notificationService.ts
│
locales/
├── en.json
├── hi.json
└── mr.json
```

---

# Navigation Architecture

expo-router provides file-based routing with native stack and tab navigators.

```
Root Layout
├── Unauthenticated: (auth)/
│       ├── /login
│       ├── /register
│       ├── /verify-otp
│       └── /forgot-password
│
└── Authenticated: (tabs)/
        ├── /                   → Home Dashboard
        ├── /reports            → My Reports
        ├── /new-report         → Submit Report
        ├── /notifications      → Notifications
        ├── /profile            → Profile & Settings
        └── /report/[id]        → Report Detail (modal stack)
```

The root layout reads authentication state from `authStore`. Unauthenticated users are redirected to `/login`.

---

# State Architecture

## Server State — React Query

All server data is managed by React Query.

| Query | Cache Key | Stale Time |
|-------|-----------|------------|
| Citizen profile | `['citizen', 'me']` | 5 minutes |
| My reports list | `['reports', citizenId]` | 1 minute |
| Report detail | `['reports', reportId]` | 30 seconds |
| Departments | `['departments']` | 1 hour |
| Notifications | `['notifications', citizenId]` | 30 seconds |

## Client State — Zustand

| Store | Responsibility | Persisted |
|-------|--------------|-----------|
| `authStore` | JWT tokens, citizen ID, login/logout | ✅ MMKV |
| `offlineStore` | Reports pending submission | ✅ MMKV |
| `settingsStore` | Language, notification preferences | ✅ MMKV |

---

# Authentication Flow

```
App launches
        │
        ▼
Read tokens from MMKV
        │
        ├── Token valid → Navigate to (tabs)/
        │
        └── Token missing or expired → Navigate to (auth)/login
```

Token refresh is handled transparently by an axios interceptor. On 401, the interceptor attempts silent refresh. If refresh fails, the citizen is logged out.

---

# Offline Support

```
Citizen submits report
        │
        ├── Network available → Submit immediately → Show tracking screen
        │
        └── Network unavailable
                        │
                        ▼
              Save report payload to MMKV offline queue
                        │
                        ▼
              Show "Saved offline" confirmation
                        │
                    (later, network restored)
                        │
                        ▼
              NetInfo triggers queue drain
                        │
                        ▼
              Submit each queued report (FIFO)
                        │
                        ▼
              Notify citizen of submission
```

Maximum offline queue size: 10 reports (configurable). Offline entries include a local UUID, timestamp, full report payload, and base64-encoded images.

---

# Component Architecture

```
Screen (page-level, data-aware)
        │
        ▼
Container Component (composition, minimal logic)
        │
        ▼
Presentational Components (stateless, pure UI)
        │
        ▼
UI Primitives (Button, Input, Card, Badge)
```

**Rules:**

- Screens are the only components that call React Query hooks
- Presentational components receive data only via props
- Business logic lives in hooks or services, not components
- All visible strings use `useTranslation()` — no hardcoded text

---

# Report Submission Flow

```
Step 1: Select issue category
Step 2: Capture or select photos (expo-image-picker)
Step 3: Describe the issue + select language
Step 4: Confirm location (GPS auto-fill + map picker)
Step 5: Review and submit
        │
        ├── Online → POST /reports → Show tracking screen
        └── Offline → Queue in MMKV → Show offline confirmation
```

The multi-step form is managed by react-hook-form with Zod validation at each step boundary.

---

# Localization

Supported languages:

| Code | Language |
|------|---------|
| `en` | English |
| `hi` | Hindi |
| `mr` | Marathi |

- Translation files in `locales/{lang}.json`
- Language auto-detected from device locale
- Manual override via profile preferences
- All user-visible strings must use `useTranslation()`

---

# Push Notifications

Notification events delivered via FCM through Expo Notifications:

| Event | Notification |
|-------|-------------|
| Report submitted | "Your report has been received." |
| Report verified | "Your report has been verified." |
| Department assigned | "Assigned to [Department]." |
| In progress | "Work has started on your report." |
| Resolved | "Your issue has been resolved." |
| Rejected | "Your report was not accepted." |

---

# Performance Targets

| Metric | Target |
|--------|--------|
| App launch to interactive | < 3 seconds |
| Report list render | < 500 ms |
| Report submission (online) | < 3 seconds |
| Offline queue drain per report | < 5 seconds |

---

# Security

| Concern | Implementation |
|---------|---------------|
| Token storage | MMKV encrypted storage |
| API communication | HTTPS only |
| Location data | Not persisted beyond active session |
| Sensitive logging | No PII in console logs or crash reports |

---

# References

- [Authentication Specification](../specs/auth.md)
- [Report Specification](../specs/reports.md)
- [API Specification](../specs/api.md)
- [ADR-005: React Query](../decisions/ADR-005-react-query.md)
- [Backend Architecture](./backend.md)
