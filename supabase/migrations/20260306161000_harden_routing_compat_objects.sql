-- Harden routing compatibility objects surfaced by database lints.

ALTER VIEW public.pj_roads
SET (security_invoker = true);

CREATE OR REPLACE FUNCTION public.refresh_pj_roads_vertices_pgr()
RETURNS void
LANGUAGE plpgsql
SET search_path = pg_catalog, public
AS $function$
BEGIN
    REFRESH MATERIALIZED VIEW public.pj_roads_vertices_pgr;
END;
$function$;

REVOKE ALL ON TABLE public.pj_roads_vertices_pgr FROM anon;
REVOKE ALL ON TABLE public.pj_roads_vertices_pgr FROM authenticated;
