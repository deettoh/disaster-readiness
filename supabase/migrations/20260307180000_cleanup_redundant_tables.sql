-- Drop redundant objects created by Python seeding scripts
-- These conflict with the view/materialized view defined in earlier migrations.

-- topology_stats_summary is never used by application code
DROP TABLE IF EXISTS public.topology_stats_summary CASCADE;

-- The raw pj_roads TABLE from the pg_dump conflicts with the VIEW defined
-- in 20260305143000_add_routing_compatibility_views.sql.
-- We only need the VIEW (derived from roads_edges).
-- Note: DROP TABLE will only succeed if import_road_edges.py created the table;
-- if the view exists instead, this is a no-op due to type mismatch (safe).
DO $$
BEGIN
    -- Check if pj_roads is a TABLE (not a view)
    IF EXISTS (
        SELECT 1 FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE c.relname = 'pj_roads'
          AND n.nspname = 'public'
          AND c.relkind = 'r'  -- 'r' = ordinary table
    ) THEN
        DROP TABLE public.pj_roads CASCADE;
        RAISE NOTICE 'Dropped redundant pj_roads TABLE';
    END IF;

    -- Check if pj_roads_vertices_pgr is a TABLE (not a materialized view)
    IF EXISTS (
        SELECT 1 FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE c.relname = 'pj_roads_vertices_pgr'
          AND n.nspname = 'public'
          AND c.relkind = 'r'  -- 'r' = ordinary table
    ) THEN
        DROP TABLE public.pj_roads_vertices_pgr CASCADE;
        RAISE NOTICE 'Dropped redundant pj_roads_vertices_pgr TABLE';
    END IF;
END $$;

-- Recreate the VIEW and MATERIALIZED VIEW from the canonical roads_edges
-- (Re-run from 20260305143000 to ensure they exist after dropping conflicting tables)

-- Drop views and materialized views first to allow altering dependent columns in roads_edges
DROP VIEW IF EXISTS public.pj_roads CASCADE;
DROP MATERIALIZED VIEW IF EXISTS public.pj_roads_vertices_pgr CASCADE;

ALTER TABLE public.roads_edges
  ALTER COLUMN source TYPE bigint,
  ALTER COLUMN target TYPE bigint;

CREATE OR REPLACE VIEW public.pj_roads AS
SELECT
    re.id,
    re.source,
    re.target,
    COALESCE(re.length, extensions.ST_Length(re.geom::extensions.geography), 0) AS length,
    COALESCE(re.base_cost, re.cost, 0) AS base_cost,
    COALESCE(re.risk_penalty, 0) AS risk_penalty,
    COALESCE(
        re.agg_cost,
        COALESCE(re.base_cost, re.cost, 0) + COALESCE(re.risk_penalty, 0)
    ) AS agg_cost,
    CASE
        WHEN re.reverse_cost = -1 THEN -1
        ELSE COALESCE(
            re.agg_reverse_cost,
            COALESCE(re.reverse_cost, COALESCE(re.base_cost, re.cost, 0))
                + COALESCE(re.risk_penalty, 0)
        )
    END AS agg_reverse_cost,
    re.geom AS geometry
FROM public.roads_edges AS re;

-- Phase 3: Fix grid_cells geometry type to support MultiPolygons from clipping
ALTER TABLE public.grid_cells
  ALTER COLUMN geom TYPE extensions.geometry(Geometry, 4326);

ALTER VIEW public.pj_roads SET (security_invoker = true);

-- Recreate materialized view (only if roads_edges has data)
DROP MATERIALIZED VIEW IF EXISTS public.pj_roads_vertices_pgr;

CREATE MATERIALIZED VIEW public.pj_roads_vertices_pgr AS
WITH node_points AS (
    SELECT
        re.source AS id,
        extensions.ST_StartPoint(re.geom) AS pt
    FROM public.roads_edges AS re
    WHERE re.source IS NOT NULL AND re.geom IS NOT NULL
    UNION ALL
    SELECT
        re.target AS id,
        extensions.ST_EndPoint(re.geom) AS pt
    FROM public.roads_edges AS re
    WHERE re.target IS NOT NULL AND re.geom IS NOT NULL
)
SELECT
    np.id::bigint AS id,
    COUNT(*)::integer AS cnt,
    extensions.ST_Centroid(extensions.ST_Collect(np.pt))::extensions.geometry(Point, 4326) AS the_geom
FROM node_points AS np
GROUP BY np.id;

CREATE UNIQUE INDEX IF NOT EXISTS pj_roads_vertices_pgr_id_idx
    ON public.pj_roads_vertices_pgr (id);

CREATE INDEX IF NOT EXISTS pj_roads_vertices_pgr_geom_idx
    ON public.pj_roads_vertices_pgr
    USING GIST (the_geom);

-- Revoke direct access on materialized view (service_role only)
REVOKE ALL ON TABLE public.pj_roads_vertices_pgr FROM anon;
REVOKE ALL ON TABLE public.pj_roads_vertices_pgr FROM authenticated;
