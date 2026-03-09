-- Readiness engine functions: hazard aggregation, score computation, alerts.
-- Source: supabase/snippets/ (hardened with SECURITY INVOKER + search_path).

-- 1. Extended hazard aggregation (wraps hazard_agg_per_cell from Phase 2).
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
SECURITY INVOKER
SET search_path TO 'pg_catalog', 'public', 'extensions'
AS $function$
  WITH base AS (
    SELECT
      hazard_count,
      avg_probability,
      dominant_type
    FROM public.hazard_agg_per_cell(p_cell_id, p_lookback_hours)
  )
  SELECT
    COALESCE(hazard_count, 0) AS hazard_count,
    COALESCE(avg_probability, 0)::numeric AS severity_weighted,
    COALESCE(avg_probability, 0)::numeric AS confidence_weighted,
    CASE
      WHEN COALESCE(hazard_count, 0) > 0 THEN 1::numeric
      ELSE 0::numeric
    END AS time_decay
  FROM base;
$function$;


-- 2. Compute readiness score for a single cell (0-100 with breakdown).
CREATE OR REPLACE FUNCTION public.compute_readiness_for_cell(
    p_cell_id integer,
    p_lookback_hours integer DEFAULT 24
)
RETURNS TABLE(
    score numeric(5,2),
    breakdown jsonb,
    coverage_confidence numeric(4,3)
)
LANGUAGE plpgsql
STABLE
SECURITY INVOKER
SET search_path TO 'pg_catalog', 'public', 'extensions'
AS $function$
DECLARE
  v_hazard_count     bigint := 0;
  v_hazard_severity  numeric := 0;
  v_time_decay       numeric := 0;
  v_vulnerability    numeric := 0;
  v_access_time_sec  numeric := NULL;
  v_coverage         numeric := 0;
  v_hazard_penalty        numeric := 0;
  v_vulnerability_penalty numeric := 0;
  v_access_bonus          numeric := 0;
  v_conf_bonus            numeric := 0;
  v_score           numeric(5,2) := 100;
BEGIN
  -- Recent hazard aggregation
  SELECT
    hazard_count,
    severity_weighted,
    time_decay
  INTO
    v_hazard_count,
    v_hazard_severity,
    v_time_decay
  FROM public.hazard_agg_per_cell_extended(p_cell_id, p_lookback_hours);

  -- Baseline vulnerability
  SELECT baseline_vulnerability
  INTO v_vulnerability
  FROM public.grid_cells
  WHERE id = p_cell_id;

  -- Accessibility input
  SELECT avg_travel_time_to_shelter_seconds
  INTO v_access_time_sec
  FROM public.cell_accessibility
  WHERE cell_id = p_cell_id;

  -- Coverage/confidence (saturates at ~20 hazards)
  v_coverage := LEAST(1.0, v_hazard_count::numeric / 20.0);

  -- Penalty/bonus components
  v_hazard_penalty := LEAST(50, v_hazard_severity * 50);
  v_vulnerability_penalty := LEAST(30, COALESCE(v_vulnerability, 0) * 30);

  IF v_access_time_sec IS NOT NULL THEN
    v_access_bonus := GREATEST(-20, 20 - (v_access_time_sec / 60.0));
  ELSE
    v_access_bonus := 0;
  END IF;

  v_conf_bonus := (v_coverage * 10);

  -- Final 0-100 score
  v_score := 100
             - v_hazard_penalty
             - v_vulnerability_penalty
             + v_access_bonus
             + v_conf_bonus;
  v_score := GREATEST(0, LEAST(100, v_score));

  RETURN QUERY
  SELECT
    v_score,
    jsonb_build_object(
      'hazard_penalty',          v_hazard_penalty,
      'vulnerability_penalty',   v_vulnerability_penalty,
      'accessibility_bonus',     v_access_bonus,
      'confidence_bonus',        v_conf_bonus,
      'hazard_count',            v_hazard_count,
      'time_decay',              v_time_decay,
      'coverage',                v_coverage
    ),
    v_coverage::numeric(4,3);
END;
$function$;


-- 3. Upsert readiness score for a cell (calls compute_readiness_for_cell).
CREATE OR REPLACE FUNCTION public.update_readiness_scores(p_cell_id integer)
RETURNS void
LANGUAGE plpgsql
VOLATILE
SECURITY INVOKER
SET search_path TO 'pg_catalog', 'public', 'extensions'
AS $function$
DECLARE
  v_score     numeric(5,2);
  v_breakdown jsonb;
  v_coverage  numeric(4,3);
BEGIN
  SELECT score, breakdown, coverage_confidence
  INTO v_score, v_breakdown, v_coverage
  FROM public.compute_readiness_for_cell(p_cell_id);

  INSERT INTO public.readiness_scores (
    cell_id,
    score,
    breakdown,
    coverage_confidence,
    updated_at
  )
  VALUES (
    p_cell_id,
    v_score,
    v_breakdown,
    v_coverage,
    now()
  )
  ON CONFLICT (cell_id)
  DO UPDATE SET
    score               = EXCLUDED.score,
    breakdown           = EXCLUDED.breakdown,
    coverage_confidence = EXCLUDED.coverage_confidence,
    updated_at          = EXCLUDED.updated_at;
END;
$function$;


-- 4. Generate alert when readiness drops below threshold.
CREATE OR REPLACE FUNCTION public.raise_alert_if_low_readiness(
    p_cell_id integer,
    p_threshold numeric DEFAULT 40
)
RETURNS void
LANGUAGE plpgsql
VOLATILE
SECURITY INVOKER
SET search_path TO 'pg_catalog', 'public', 'extensions'
AS $function$
DECLARE
  v_score numeric(5,2);
BEGIN
  SELECT score
  INTO v_score
  FROM public.readiness_scores
  WHERE cell_id = p_cell_id;

  IF v_score IS NOT NULL AND v_score < p_threshold THEN
    INSERT INTO public.alerts (cell_id, severity, message)
    VALUES (
      p_cell_id,
      'high',
      format('Readiness dropped below %s (%s)', p_threshold, round(v_score, 2))
    );
  END IF;
END;
$function$;


-- 5. Generate alert for high-probability severe hazards.
CREATE OR REPLACE FUNCTION public.raise_alert_for_severe_hazard(
    p_prediction_id uuid,
    p_cell_id integer,
    p_image_id uuid DEFAULT NULL
)
RETURNS void
LANGUAGE plpgsql
VOLATILE
SECURITY INVOKER
SET search_path TO 'pg_catalog', 'public', 'extensions'
AS $function$
DECLARE
  v_type    text;
  v_prob    numeric;
  v_message text;
BEGIN
  SELECT prediction_type, probability
  INTO v_type, v_prob
  FROM public.hazard_predictions
  WHERE id = p_prediction_id;

  IF v_prob IS NOT NULL AND v_prob >= 0.9 THEN
    v_message := format(
      'Severe %s detected (p=%s)',
      coalesce(v_type, 'hazard'),
      round(v_prob, 2)
    );

    INSERT INTO public.alerts (cell_id, severity, message)
    VALUES (p_cell_id, 'high', v_message);
  END IF;
END;
$function$;
