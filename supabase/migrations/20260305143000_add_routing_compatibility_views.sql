-- Compatibility shim for routing contract:
-- Keep public.roads_edges as canonical source while exposing legacy objects
-- expected by routing/sql/contract.py (pj_roads, pj_roads_vertices_pgr).

ALTER TABLE public.roads_edges
ADD COLUMN IF NOT EXISTS base_cost double precision;

ALTER TABLE public.roads_edges
ADD COLUMN IF NOT EXISTS risk_penalty double precision DEFAULT 0;

ALTER TABLE public.roads_edges
ADD COLUMN IF NOT EXISTS agg_cost double precision;

ALTER TABLE public.roads_edges
ADD COLUMN IF NOT EXISTS agg_reverse_cost double precision;

ALTER TABLE public.roads_edges
ADD COLUMN IF NOT EXISTS length double precision;

UPDATE public.roads_edges
SET
    base_cost = COALESCE(base_cost, cost, 0),
    risk_penalty = COALESCE(risk_penalty, 0),
    agg_cost = COALESCE(base_cost, cost, 0) + COALESCE(risk_penalty, 0),
    agg_reverse_cost = CASE
        WHEN reverse_cost = -1 THEN -1
        ELSE COALESCE(reverse_cost, COALESCE(base_cost, cost, 0))
            + COALESCE(risk_penalty, 0)
    END,
    length = COALESCE(length, extensions.ST_Length(geom::extensions.geography), 0);

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

CREATE OR REPLACE FUNCTION public.refresh_pj_roads_vertices_pgr()
RETURNS void
LANGUAGE plpgsql
AS $function$
BEGIN
    REFRESH MATERIALIZED VIEW public.pj_roads_vertices_pgr;
END;
$function$;
