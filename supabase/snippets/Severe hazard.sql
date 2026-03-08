CREATE OR REPLACE FUNCTION public.raise_alert_for_severe_hazard(
    p_prediction_id uuid,
    p_cell_id integer,
    p_image_id uuid DEFAULT NULL 
)
RETURNS void
LANGUAGE plpgsql
VOLATILE
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
      'Severe %s detected (p=%.2f)',
      coalesce(v_type, 'hazard'),
      v_prob
    );

    INSERT INTO public.alerts (cell_id, severity, message)
    VALUES (p_cell_id, 'high', v_message);

    
  END IF;
END;
$function$;
