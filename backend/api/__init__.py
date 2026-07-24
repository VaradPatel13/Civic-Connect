"""FastAPI API routes for CivicConnect.

Routes organized by domain:
- auth: Authentication endpoints (register, login, OTP)
- reports: Report CRUD and submission
- agents: Agent pipeline triggers
- notifications: WebSocket endpoints
- rewards: Points and leaderboard

All routes require JWT authentication unless explicitly public.
"""
