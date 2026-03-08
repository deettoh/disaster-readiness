CREATE OR REPLACE FUNCTION public.update_readiness_scores(p_cell_id integer)
RETURNS void
LANGUAGE plpgsql
VOLATILE
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
