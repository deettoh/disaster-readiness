# Supabase (Database + Storage)

This directory contains the Supabase project configuration, SQL migrations, seed data, and helper scripts for the PostgreSQL + PostGIS + pgRouting database that powers the Hyperlocal Disaster Readiness platform.

## Folder Structure

```text
supabase/
├── migrations/             # Sequential SQL migration files for PostGIS + pgRouting
└── scripts/                # Helper Python scripts (e.g., initialize_readiness.py)
```

## Extensions

The database has the following extensions enabled:

- **PostGIS** — spatial data types and geospatial queries
- **pgRouting** — graph-based shortest-path routing
- **uuid-ossp** — UUID generation for primary keys

## Migrations

Migrations are in `supabase/migrations/` and applied in order:

| Migration | Purpose |
| --- | --- |
| `20260301172229_remote_schema.sql` | Initial schema bootstrap |
| `20260301173126_remote_schema.sql` | Core tables: `reports`, `images`, `hazard_predictions`, `grid_cells`, `neighborhoods`, `readiness_scores`, `alerts`, `roads_edges`, `shelters`, `weather_snapshots`, `cell_accessibility` |
| `20260304160032_add_images_bucket.sql` | Supabase Storage bucket + policies for redacted images |
| `20260305143000_add_routing_compatibility_views.sql` | Compatibility views (`pj_roads`, `pj_roads_vertices_pgr`) backed by canonical `roads_edges` |
| `20260306161000_harden_routing_compat_objects.sql` | Security hardening on routing compatibility objects |
| `20260306170000_indexes_rls_functions.sql` | B-tree/GIST indexes, RLS policies, spatial helper functions (`point_to_cell`, `nearest_shelters`, `roads_near_hazard`, `hazard_agg_per_cell`) |
| `20260307180000_cleanup_redundant_tables.sql` | Removes legacy/redundant schema objects |
| `20260308134636_remote_schema.sql` | Additional schema sync |
| `20260310000000_readiness_engine_functions.sql` | Readiness score computation functions (`compute_readiness_for_cell`, `update_readiness_scores`) and alert generation |

## Seed Data

- `seed.sql` — static reference data (shelters, initial config) applied automatically by `supabase db reset`
- Heavy spatial data (roads, grid cells, accessibility metrics) is loaded by Python scripts in `routing/scripts/` — see [routing/README.md](../routing/README.md)

## Helper Scripts

- `supabase/scripts/initialize_readiness.py` — compute initial readiness scores for all grid cells after seeding

## Common Commands

```bash
# Reset local DB (applies migrations + seed.sql)
supabase db reset

# Push migrations to linked remote Supabase
supabase db push

# Check for schema drift against linked DB
supabase db diff --linked --schema public

# Generate a new migration
supabase migration new <migration_name>
```

## Key Functions (SQL)

| Function | Purpose |
| --- | --- |
| `point_to_cell(geom)` | Map a point geometry to its containing grid cell |
| `nearest_shelters(geom, limit)` | Find closest shelters to a given point |
| `roads_near_hazard(geom, radius)` | Find road edges within radius of a hazard |
| `hazard_agg_per_cell(cell_id)` | Aggregate recent hazards for a grid cell |
| `compute_readiness_for_cell(cell_id)` | Compute readiness score with breakdown JSON |
| `update_readiness_scores()` | Batch recompute all readiness scores |
