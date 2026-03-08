-- FK B-tree indexes on columns not already covered by PKs
CREATE INDEX IF NOT EXISTS idx_images_report_id
    ON public.images USING btree (report_id);

CREATE INDEX IF NOT EXISTS idx_alerts_cell_id
    ON public.alerts USING btree (cell_id);

CREATE INDEX IF NOT EXISTS idx_weather_snapshots_cell_id
    ON public.weather_snapshots USING btree (cell_id);

-- GIST index on hazard_predictions geometry for spatial queries
CREATE INDEX IF NOT EXISTS idx_hazard_predictions_geom
    ON public.hazard_predictions USING gist (geom);


-- RLS policies

-- Pattern per table:
--   anon + authenticated: SELECT only (public read for map layers)
--   service_role: ALL (backend writes)
--   reports: additionally allow anon/authenticated INSERT


-- reports --
DROP POLICY IF EXISTS "Allow public read on reports" ON public.reports;
CREATE POLICY "Allow public read on reports"
    ON public.reports FOR SELECT
    TO anon, authenticated
    USING (true);

DROP POLICY IF EXISTS "Allow public insert on reports" ON public.reports;
CREATE POLICY "Allow public insert on reports"
    ON public.reports FOR INSERT
    TO anon, authenticated
    WITH CHECK (true);

DROP POLICY IF EXISTS "Service role full access on reports" ON public.reports;
CREATE POLICY "Service role full access on reports"
    ON public.reports FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- images --
DROP POLICY IF EXISTS "Allow public read on images" ON public.images;
CREATE POLICY "Allow public read on images"
    ON public.images FOR SELECT
    TO anon, authenticated
    USING (true);

DROP POLICY IF EXISTS "Service role full access on images" ON public.images;
CREATE POLICY "Service role full access on images"
    ON public.images FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- hazard_predictions --
DROP POLICY IF EXISTS "Allow public read on hazard_predictions" ON public.hazard_predictions;
CREATE POLICY "Allow public read on hazard_predictions"
    ON public.hazard_predictions FOR SELECT
    TO anon, authenticated
    USING (true);

DROP POLICY IF EXISTS "Service role full access on hazard_predictions" ON public.hazard_predictions;
CREATE POLICY "Service role full access on hazard_predictions"
    ON public.hazard_predictions FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- grid_cells --
DROP POLICY IF EXISTS "Allow public read on grid_cells" ON public.grid_cells;
CREATE POLICY "Allow public read on grid_cells"
    ON public.grid_cells FOR SELECT
    TO anon, authenticated
    USING (true);

DROP POLICY IF EXISTS "Service role full access on grid_cells" ON public.grid_cells;
CREATE POLICY "Service role full access on grid_cells"
    ON public.grid_cells FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- readiness_scores --
DROP POLICY IF EXISTS "Allow public read on readiness_scores" ON public.readiness_scores;
CREATE POLICY "Allow public read on readiness_scores"
    ON public.readiness_scores FOR SELECT
    TO anon, authenticated
    USING (true);

DROP POLICY IF EXISTS "Service role full access on readiness_scores" ON public.readiness_scores;
CREATE POLICY "Service role full access on readiness_scores"
    ON public.readiness_scores FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- alerts --
DROP POLICY IF EXISTS "Allow public read on alerts" ON public.alerts;
CREATE POLICY "Allow public read on alerts"
    ON public.alerts FOR SELECT
    TO anon, authenticated
    USING (true);

DROP POLICY IF EXISTS "Service role full access on alerts" ON public.alerts;
CREATE POLICY "Service role full access on alerts"
    ON public.alerts FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- roads_edges --
DROP POLICY IF EXISTS "Allow public read on roads_edges" ON public.roads_edges;
CREATE POLICY "Allow public read on roads_edges"
    ON public.roads_edges FOR SELECT
    TO anon, authenticated
    USING (true);

DROP POLICY IF EXISTS "Service role full access on roads_edges" ON public.roads_edges;
CREATE POLICY "Service role full access on roads_edges"
    ON public.roads_edges FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- shelters --
DROP POLICY IF EXISTS "Allow public read on shelters" ON public.shelters;
CREATE POLICY "Allow public read on shelters"
    ON public.shelters FOR SELECT
    TO anon, authenticated
    USING (true);

DROP POLICY IF EXISTS "Service role full access on shelters" ON public.shelters;
CREATE POLICY "Service role full access on shelters"
    ON public.shelters FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- cell_accessibility --
DROP POLICY IF EXISTS "Allow public read on cell_accessibility" ON public.cell_accessibility;
CREATE POLICY "Allow public read on cell_accessibility"
    ON public.cell_accessibility FOR SELECT
    TO anon, authenticated
    USING (true);

DROP POLICY IF EXISTS "Service role full access on cell_accessibility" ON public.cell_accessibility;
CREATE POLICY "Service role full access on cell_accessibility"
    ON public.cell_accessibility FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- weather_snapshots --
DROP POLICY IF EXISTS "Allow public read on weather_snapshots" ON public.weather_snapshots;
CREATE POLICY "Allow public read on weather_snapshots"
    ON public.weather_snapshots FOR SELECT
    TO anon, authenticated
    USING (true);

DROP POLICY IF EXISTS "Service role full access on weather_snapshots" ON public.weather_snapshots;
CREATE POLICY "Service role full access on weather_snapshots"
    ON public.weather_snapshots FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- neighborhoods --
DROP POLICY IF EXISTS "Allow public read on neighborhoods" ON public.neighborhoods;
CREATE POLICY "Allow public read on neighborhoods"
    ON public.neighborhoods FOR SELECT
    TO anon, authenticated
    USING (true);

DROP POLICY IF EXISTS "Service role full access on neighborhoods" ON public.neighborhoods;
CREATE POLICY "Service role full access on neighborhoods"
    ON public.neighborhoods FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);



-- Spatial helper functions 

-- Point to grid cell lookup
-- Returns the integer id of the grid cell that contains the given point,
-- or NULL if no cell contains it.
CREATE OR REPLACE FUNCTION public.point_to_cell(
    p_lng double precision,
    p_lat double precision
)
RETURNS integer
LANGUAGE sql
STABLE
SECURITY INVOKER
SET search_path = pg_catalog, public, extensions
AS $$
    SELECT gc.id
    FROM public.grid_cells AS gc
    WHERE extensions.ST_Contains(
        gc.geom,
        extensions.ST_SetSRID(extensions.ST_MakePoint(p_lng, p_lat), 4326)
    )
    LIMIT 1;
$$;

-- Nearest shelters lookup
-- Returns the closest shelters to the given point, ordered by distance.
CREATE OR REPLACE FUNCTION public.nearest_shelters(
    p_lng double precision,
    p_lat double precision,
    p_limit integer DEFAULT 3
)
RETURNS TABLE (
    shelter_id integer,
    shelter_name text,
    capacity integer,
    distance_meters double precision
)
LANGUAGE sql
STABLE
SECURITY INVOKER
SET search_path = pg_catalog, public, extensions
AS $$
    SELECT
        s.id,
        s.name,
        s.capacity,
        extensions.ST_Distance(
            s.geom,
            extensions.ST_SetSRID(
                extensions.ST_MakePoint(p_lng, p_lat)::extensions.geography,
                4326
            )
        ) AS distance_meters
    FROM public.shelters AS s
    ORDER BY distance_meters
    LIMIT p_limit;
$$;

-- Roads near hazard point
-- Returns road edge IDs within the given radius of a hazard point.
CREATE OR REPLACE FUNCTION public.roads_near_hazard(
    p_lng double precision,
    p_lat double precision,
    p_radius_m double precision DEFAULT 500
)
RETURNS TABLE (
    edge_id integer,
    distance_meters double precision
)
LANGUAGE sql
STABLE
SECURITY INVOKER
SET search_path = pg_catalog, public, extensions
AS $$
    SELECT
        re.id,
        extensions.ST_Distance(
            re.geom::extensions.geography,
            extensions.ST_SetSRID(extensions.ST_MakePoint(p_lng, p_lat), 4326)::extensions.geography
        ) AS distance_meters
    FROM public.roads_edges AS re
    WHERE extensions.ST_DWithin(
        re.geom::extensions.geography,
        extensions.ST_SetSRID(extensions.ST_MakePoint(p_lng, p_lat), 4326)::extensions.geography,
        p_radius_m
    )
    ORDER BY distance_meters;
$$;

-- Hazard aggregation per grid cell
-- Aggregates recent hazard predictions that fall within a given cell.
-- Returns count, confidence-weighted severity sum, and the dominant hazard type.
CREATE OR REPLACE FUNCTION public.hazard_agg_per_cell(
    p_cell_id integer,
    p_lookback_hours integer DEFAULT 24
)
RETURNS TABLE (
    hazard_count bigint,
    avg_probability numeric,
    dominant_type text
)
LANGUAGE sql
STABLE
SECURITY INVOKER
SET search_path = pg_catalog, public, extensions
AS $$
    WITH cell_hazards AS (
        SELECT hp.prediction_type, hp.probability
        FROM public.hazard_predictions AS hp
        JOIN public.grid_cells AS gc ON extensions.ST_Contains(
            gc.geom,
            extensions.ST_SetSRID(
                extensions.ST_MakePoint(
                    extensions.ST_X(hp.geom::extensions.geometry),
                    extensions.ST_Y(hp.geom::extensions.geometry)
                ),
                4326
            )
        )
        WHERE gc.id = p_cell_id
          AND hp.created_at >= (now() - make_interval(hours => p_lookback_hours))
    ),
    dominant AS (
        SELECT prediction_type, COUNT(*) AS cnt
        FROM cell_hazards
        GROUP BY prediction_type
        ORDER BY cnt DESC
        LIMIT 1
    )
    SELECT
        COUNT(*)::bigint AS hazard_count,
        AVG(ch.probability) AS avg_probability,
        (SELECT d.prediction_type FROM dominant AS d) AS dominant_type
    FROM cell_hazards AS ch;
$$;
