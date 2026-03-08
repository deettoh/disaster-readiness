drop view if exists "public"."pj_roads";

drop materialized view if exists "public"."pj_roads_vertices_pgr";

create or replace view "public"."pj_roads" as  SELECT id,
    source,
    target,
    COALESCE(length, extensions.st_length((geom)::extensions.geography), (0)::double precision) AS length,
    COALESCE(base_cost, cost, (0)::double precision) AS base_cost,
    COALESCE(risk_penalty, (0)::double precision) AS risk_penalty,
    COALESCE(agg_cost, (COALESCE(base_cost, cost, (0)::double precision) + COALESCE(risk_penalty, (0)::double precision))) AS agg_cost,
        CASE
            WHEN (reverse_cost = ('-1'::integer)::double precision) THEN ('-1'::integer)::double precision
            ELSE COALESCE(agg_reverse_cost, (COALESCE(reverse_cost, COALESCE(base_cost, cost, (0)::double precision)) + COALESCE(risk_penalty, (0)::double precision)))
        END AS agg_reverse_cost,
    geom AS geometry
   FROM public.roads_edges re;


create materialized view "public"."pj_roads_vertices_pgr" as  WITH node_points AS (
         SELECT re.source AS id,
            extensions.st_startpoint(re.geom) AS pt
           FROM public.roads_edges re
          WHERE ((re.source IS NOT NULL) AND (re.geom IS NOT NULL))
        UNION ALL
         SELECT re.target AS id,
            extensions.st_endpoint(re.geom) AS pt
           FROM public.roads_edges re
          WHERE ((re.target IS NOT NULL) AND (re.geom IS NOT NULL))
        )
 SELECT id,
    (count(*))::integer AS cnt,
    (extensions.st_centroid(extensions.st_collect(pt)))::extensions.geometry(Point,4326) AS the_geom
   FROM node_points np
  GROUP BY id;



