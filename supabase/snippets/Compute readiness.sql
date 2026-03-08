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
SET search_path TO 'pg_catalog', 'public', 'extensions'
AS $function$
DECLARE
  -- Hazard aggregation outputs
  v_hazard_count     bigint := 0;
  v_hazard_severity  numeric := 0;  
  v_time_decay       numeric := 0;

  -- Vulnerability & accessibility
  v_vulnerability    numeric := 0;   
  v_access_time_sec  numeric := NULL;

  -- Coverage / confidence
  v_coverage         numeric := 0;

  -- Score components
  v_hazard_penalty        numeric := 0;
  v_vulnerability_penalty numeric := 0;
  v_access_bonus          numeric := 0;
  v_conf_bonus            numeric := 0;

  v_score           numeric(5,2) := 100;
BEGIN
--Recent hazard aggregation
 
  SELECT
    hazard_count,
    severity_weighted,
    time_decay
  INTO
    v_hazard_count,
    v_hazard_severity,
    v_time_decay
  FROM public.hazard_agg_per_cell_extended(p_cell_id, p_lookback_hours);

  --Baseline vulnerability
  
  SELECT baseline_vulnerability
  INTO v_vulnerability
  FROM public.grid_cells
  WHERE id = p_cell_id;


  --Accessibility input
  
  SELECT avg_travel_time_to_shelter_seconds
  INTO v_access_time_sec
  FROM public.cell_accessibility
  WHERE cell_id = p_cell_id;

  
  --Coverage/confidence
  --------------------------------------------------------------------
  v_coverage := LEAST(1.0, v_hazard_count::numeric / 20.0);

  
  v_hazard_penalty := LEAST(50, v_hazard_severity * 50);
  v_vulnerability_penalty := LEAST(30, v_vulnerability * 30);

  IF v_access_time_sec IS NOT NULL THEN
    v_access_bonus := GREATEST(-20, 20 - (v_access_time_sec / 60.0));
  ELSE
    v_access_bonus := 0;  
  END IF;

  v_conf_bonus := (v_coverage * 10);

  -- 0–100 score
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
