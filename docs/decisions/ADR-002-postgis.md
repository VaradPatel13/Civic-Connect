# ADR-002: Selection of PostGIS for Geospatial Storage and Routing

- **Status**: Accepted
- **Date**: 2026-07-23
- **Deciders**: Database & Backend Architecture Team

---

# Context

CivicConnect must accurately map citizen report coordinates (latitude/longitude) to municipal wards, administrative boundaries, and department jurisdictions across the Pune Municipal Corporation (PMC). We needed a spatially-aware database extension compatible with PostgreSQL.

# Considered Options

1. **Elasticsearch Geospatial Queries**: Good search performance, but adds dual-write complexity and database synchronization overhead.
2. **PostgreSQL native Point types**: Insufficient for complex spatial operations (polygons, spatial indexing, ST_Contains, ST_Intersects).
3. **PostGIS (PostgreSQL Extension)**: Industry-standard spatial database engine natively extending PostgreSQL.

# Decision

We selected **PostGIS** as our spatial engine.

# Rationale

- **Native SQL Integration**: Seamlessly queries spatial polygons and point coordinates within SQLAlchemy and Alembic migrations.
- **High Performance Spatial Indexing**: R-Tree spatial indexing (`GIST`) provides sub-50ms point-in-polygon queries for ward assignment.
- **Standardized Coordinate System**: Native support for WGS 84 (`EPSG:4326`).
- **Single Database Solution**: Eliminates secondary database synchronization risks.

# Consequences

- **Positive**: High accuracy spatial matching, native SQLAlchemy integration (`GeoAlchemy2`), simplified infrastructure.
- **Negative**: Requires PostGIS-enabled PostgreSQL container images (`postgis/postgis`).
