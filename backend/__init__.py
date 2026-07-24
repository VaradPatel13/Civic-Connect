"""CivicConnect backend package for civic issue reporting.

This package contains:
- api: FastAPI route handlers
- agents: LangGraph agent pipeline (validation, forensics, classifier, etc.)
- models: SQLAlchemy database models (Citizen, Report, Photo, etc.)
- schemas: Pydantic request/response validation schemas
- services: Business logic layer
- tasks: Celery background tasks
- core: Configuration, security, database utilities
"""
