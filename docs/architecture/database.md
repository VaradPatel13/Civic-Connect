# Database Architecture

## Overview

CivicConnect uses PostgreSQL 16 with PostGIS extension for geospatial capabilities. This document describes the database schema and design decisions.

## Key Features

### Geospatial Support

PostGIS enables:

- Ward boundary containment checks
- Location-based routing
- Distance calculations for reporting

### Audit Trail

All agent decisions are logged for transparency:

- Immutable execution history
- Input/output snapshots
- Confidence scores and timing

### Multi-Tenant Design

Though starting as a single-city (Pune Municipal Corporation) deployment, the schema supports:

- Multiple cities
- Hierarchical ward boundaries
- Department-specific routing rules

## References

- [Database Schema](../specs/database.md)
- [Agent Pipeline](../specs/ai-pipeline.md)