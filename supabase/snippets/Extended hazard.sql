CREATE OR REPLACE FUNCTION public.hazard_agg_per_cell_extended(
  p_cell_id integer,
  p_lookback_hours integer DEFAULT 24
)
RETURNS TABLE (
  hazard_count bigint,
  severity_weighted numeric,
  confidence_weighted numeric,
  time_decay numeric
)
LANGUAGE sql
STABLE
SET search_path TO 'pg_catalog', 'public', 'extensions'
AS $function$
  -- Reuse your existing aggregation
  WITH base AS (
    SELECT
      hazard_count,
      avg_probability,
      dominant_type
    FROM public.hazard_agg_per_cell(p_cell_id, p_lookback_hours)
  )
  SELECT
    COALESCE(hazard_count, 0) AS hazard_count,
    -- Treat avg_probability as a “severity-like” 0–1 term for now
    COALESCE(avg_probability, 0)::numeric AS severity_weighted,
    -- Also reuse it as a confidence-weighted signal (can change later)
    COALESCE(avg_probability, 0)::numeric AS confidence_weighted,
    -- Simple placeholder for time_decay: 1 if any hazards in window, 0 if none
    CASE
      WHEN COALESCE(hazard_count, 0) > 0 THEN 1::numeric
      ELSE 0::numeric
    END AS time_decay
  FROM base;
$function$;
