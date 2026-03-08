CREATE OR REPLACE FUNCTION public.raise_alert_if_low_readiness(
    p_cell_id integer,
    p_threshold numeric DEFAULT 40 
)
RETURNS void
LANGUAGE plpgsql
VOLATILE
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
      format('Readiness dropped below %s (%.2f)', p_threshold, v_score)
    );
    
  END IF;
END;
$function$;
