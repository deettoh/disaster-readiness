drop extension if exists "pg_net";

create schema if not exists "Disaster Readiness";

create schema if not exists "disaster_readiness";

create extension if not exists "pgrouting" with schema "disaster_readiness";

create extension if not exists "postgis" with schema "disaster_readiness";

create type "disaster_readiness"."hazard_type" as enum ('flood', 'landslide', 'fallen_tree', 'road_block', 'infrastructure_failure', 'other');

create sequence "public"."grid_cells_id_seq";

create sequence "public"."roads_edges_id_seq";

create sequence "public"."shelters_id_seq";


  create table "disaster_readiness"."neighborhoods" (
    "id" uuid not null default gen_random_uuid(),
    "name" text not null default ''::text,
    "code" text,
    "description" text
      );


alter table "disaster_readiness"."neighborhoods" enable row level security;


  create table "public"."alerts" (
    "id" uuid not null default gen_random_uuid(),
    "cell_id" integer,
    "severity" text,
    "message" text,
    "triggered_at" timestamp with time zone default now(),
    "resolved_at" timestamp with time zone
      );


alter table "public"."alerts" enable row level security;


  create table "public"."cell_accessibility" (
    "cell_id" integer not null,
    "avg_travel_time_to_shelter_seconds" integer,
    "avg_road_density" numeric(8,3),
    "updated_at" timestamp with time zone default now()
      );


alter table "public"."cell_accessibility" enable row level security;


  create table "public"."grid_cells" (
    "id" integer not null default nextval('public.grid_cells_id_seq'::regclass),
    "cell_id" text,
    "geom" disaster_readiness.geometry(Polygon,4326),
    "neighborhood" text,
    "baseline_vulnerability" numeric(4,3),
    "created_at" timestamp with time zone default now()
      );


alter table "public"."grid_cells" enable row level security;


  create table "public"."hazard_predictions" (
    "id" uuid not null default gen_random_uuid(),
    "geom" disaster_readiness.geography(Point,4326),
    "prediction_type" text,
    "probability" numeric(4,3),
    "model_version" text,
    "valid_from" timestamp with time zone,
    "valid_until" timestamp with time zone,
    "created_at" timestamp with time zone default now()
      );


alter table "public"."hazard_predictions" enable row level security;


  create table "public"."images" (
    "id" uuid not null default gen_random_uuid(),
    "report_id" uuid,
    "bucket_path" text not null,
    "caption" text,
    "uploaded_at" timestamp with time zone default now()
      );


alter table "public"."images" enable row level security;


  create table "public"."readiness_scores" (
    "cell_id" integer not null,
    "score" numeric(5,2),
    "breakdown" jsonb,
    "coverage_confidence" numeric(4,3),
    "updated_at" timestamp with time zone default now()
      );


alter table "public"."readiness_scores" enable row level security;


  create table "public"."reports" (
    "id" uuid not null default gen_random_uuid(),
    "geom" disaster_readiness.geography(Point,4326),
    "hazard_type" text,
    "confidence" numeric(4,2),
    "source" text,
    "metadata" jsonb,
    "created_at" timestamp with time zone default now()
      );


alter table "public"."reports" enable row level security;


  create table "public"."roads_edges" (
    "id" integer not null default nextval('public.roads_edges_id_seq'::regclass),
    "source" integer,
    "target" integer,
    "cost" double precision,
    "reverse_cost" double precision,
    "geom" disaster_readiness.geometry(LineString,4326)
      );


alter table "public"."roads_edges" enable row level security;


  create table "public"."shelters" (
    "id" integer not null default nextval('public.shelters_id_seq'::regclass),
    "name" text,
    "capacity" integer,
    "geom" disaster_readiness.geography(Point,4326),
    "address" text,
    "created_at" timestamp with time zone default now()
      );


alter table "public"."shelters" enable row level security;


  create table "public"."weather_snapshots" (
    "id" uuid not null default gen_random_uuid(),
    "cell_id" integer,
    "timestamp" timestamp with time zone not null,
    "data" jsonb,
    "created_at" timestamp with time zone default now()
      );


alter table "public"."weather_snapshots" enable row level security;

alter sequence "public"."grid_cells_id_seq" owned by "public"."grid_cells"."id";

alter sequence "public"."roads_edges_id_seq" owned by "public"."roads_edges"."id";

alter sequence "public"."shelters_id_seq" owned by "public"."shelters"."id";

CREATE UNIQUE INDEX alerts_pkey ON public.alerts USING btree (id);

CREATE UNIQUE INDEX cell_accessibility_pkey ON public.cell_accessibility USING btree (cell_id);

CREATE UNIQUE INDEX grid_cells_cell_id_key ON public.grid_cells USING btree (cell_id);

CREATE UNIQUE INDEX grid_cells_pkey ON public.grid_cells USING btree (id);

CREATE UNIQUE INDEX hazard_predictions_pkey ON public.hazard_predictions USING btree (id);

CREATE INDEX idx_alerts_triggered_at ON public.alerts USING btree (triggered_at);

CREATE INDEX idx_grid_cells_geom ON public.grid_cells USING gist (geom);

CREATE INDEX idx_hazard_predictions_valid_until ON public.hazard_predictions USING btree (valid_until);

CREATE INDEX idx_reports_created_at ON public.reports USING btree (created_at);

CREATE INDEX idx_reports_geom ON public.reports USING gist (geom);

CREATE INDEX idx_roads_edges_geom ON public.roads_edges USING gist (geom);

CREATE INDEX idx_shelters_geom ON public.shelters USING gist (geom);

CREATE INDEX idx_weather_snapshots_timestamp ON public.weather_snapshots USING btree ("timestamp");

CREATE UNIQUE INDEX images_pkey ON public.images USING btree (id);

CREATE UNIQUE INDEX readiness_scores_pkey ON public.readiness_scores USING btree (cell_id);

CREATE UNIQUE INDEX reports_pkey ON public.reports USING btree (id);

CREATE UNIQUE INDEX roads_edges_pkey ON public.roads_edges USING btree (id);

CREATE UNIQUE INDEX shelters_pkey ON public.shelters USING btree (id);

CREATE UNIQUE INDEX weather_snapshots_pkey ON public.weather_snapshots USING btree (id);

alter table "public"."alerts" add constraint "alerts_pkey" PRIMARY KEY using index "alerts_pkey";

alter table "public"."cell_accessibility" add constraint "cell_accessibility_pkey" PRIMARY KEY using index "cell_accessibility_pkey";

alter table "public"."grid_cells" add constraint "grid_cells_pkey" PRIMARY KEY using index "grid_cells_pkey";

alter table "public"."hazard_predictions" add constraint "hazard_predictions_pkey" PRIMARY KEY using index "hazard_predictions_pkey";

alter table "public"."images" add constraint "images_pkey" PRIMARY KEY using index "images_pkey";

alter table "public"."readiness_scores" add constraint "readiness_scores_pkey" PRIMARY KEY using index "readiness_scores_pkey";

alter table "public"."reports" add constraint "reports_pkey" PRIMARY KEY using index "reports_pkey";

alter table "public"."roads_edges" add constraint "roads_edges_pkey" PRIMARY KEY using index "roads_edges_pkey";

alter table "public"."shelters" add constraint "shelters_pkey" PRIMARY KEY using index "shelters_pkey";

alter table "public"."weather_snapshots" add constraint "weather_snapshots_pkey" PRIMARY KEY using index "weather_snapshots_pkey";

alter table "public"."alerts" add constraint "alerts_cell_id_fkey" FOREIGN KEY (cell_id) REFERENCES public.grid_cells(id) ON DELETE CASCADE not valid;

alter table "public"."alerts" validate constraint "alerts_cell_id_fkey";

alter table "public"."alerts" add constraint "alerts_severity_check" CHECK ((severity = ANY (ARRAY['low'::text, 'medium'::text, 'high'::text]))) not valid;

alter table "public"."alerts" validate constraint "alerts_severity_check";

alter table "public"."cell_accessibility" add constraint "cell_accessibility_cell_id_fkey" FOREIGN KEY (cell_id) REFERENCES public.grid_cells(id) ON DELETE CASCADE not valid;

alter table "public"."cell_accessibility" validate constraint "cell_accessibility_cell_id_fkey";

alter table "public"."grid_cells" add constraint "grid_cells_cell_id_key" UNIQUE using index "grid_cells_cell_id_key";

alter table "public"."images" add constraint "images_report_id_fkey" FOREIGN KEY (report_id) REFERENCES public.reports(id) ON DELETE CASCADE not valid;

alter table "public"."images" validate constraint "images_report_id_fkey";

alter table "public"."readiness_scores" add constraint "readiness_scores_cell_id_fkey" FOREIGN KEY (cell_id) REFERENCES public.grid_cells(id) ON DELETE CASCADE not valid;

alter table "public"."readiness_scores" validate constraint "readiness_scores_cell_id_fkey";

alter table "public"."readiness_scores" add constraint "readiness_scores_score_check" CHECK (((score >= (0)::numeric) AND (score <= (100)::numeric))) not valid;

alter table "public"."readiness_scores" validate constraint "readiness_scores_score_check";

alter table "public"."weather_snapshots" add constraint "weather_snapshots_cell_id_fkey" FOREIGN KEY (cell_id) REFERENCES public.grid_cells(id) ON DELETE CASCADE not valid;

alter table "public"."weather_snapshots" validate constraint "weather_snapshots_cell_id_fkey";

set check_function_bodies = off;

create type "disaster_readiness"."geometry_dump" as ("path" integer[], "geom" disaster_readiness.geometry);

create type "disaster_readiness"."valid_detail" as ("valid" boolean, "reason" character varying, "location" disaster_readiness.geometry);

CREATE OR REPLACE FUNCTION public.rls_auto_enable()
 RETURNS event_trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'pg_catalog'
AS $function$
DECLARE
  cmd record;
BEGIN
  FOR cmd IN
    SELECT *
    FROM pg_event_trigger_ddl_commands()
    WHERE command_tag IN ('CREATE TABLE', 'CREATE TABLE AS', 'SELECT INTO')
      AND object_type IN ('table','partitioned table')
  LOOP
     IF cmd.schema_name IS NOT NULL AND cmd.schema_name IN ('public') AND cmd.schema_name NOT IN ('pg_catalog','information_schema') AND cmd.schema_name NOT LIKE 'pg_toast%' AND cmd.schema_name NOT LIKE 'pg_temp%' THEN
      BEGIN
        EXECUTE format('alter table if exists %s enable row level security', cmd.object_identity);
        RAISE LOG 'rls_auto_enable: enabled RLS on %', cmd.object_identity;
      EXCEPTION
        WHEN OTHERS THEN
          RAISE LOG 'rls_auto_enable: failed to enable RLS on %', cmd.object_identity;
      END;
     ELSE
        RAISE LOG 'rls_auto_enable: skip % (either system schema or not in enforced list: %.)', cmd.object_identity, cmd.schema_name;
     END IF;
  END LOOP;
END;
$function$
;

grant delete on table "public"."alerts" to "anon";

grant insert on table "public"."alerts" to "anon";

grant references on table "public"."alerts" to "anon";

grant select on table "public"."alerts" to "anon";

grant trigger on table "public"."alerts" to "anon";

grant truncate on table "public"."alerts" to "anon";

grant update on table "public"."alerts" to "anon";

grant delete on table "public"."alerts" to "authenticated";

grant insert on table "public"."alerts" to "authenticated";

grant references on table "public"."alerts" to "authenticated";

grant select on table "public"."alerts" to "authenticated";

grant trigger on table "public"."alerts" to "authenticated";

grant truncate on table "public"."alerts" to "authenticated";

grant update on table "public"."alerts" to "authenticated";

grant delete on table "public"."alerts" to "service_role";

grant insert on table "public"."alerts" to "service_role";

grant references on table "public"."alerts" to "service_role";

grant select on table "public"."alerts" to "service_role";

grant trigger on table "public"."alerts" to "service_role";

grant truncate on table "public"."alerts" to "service_role";

grant update on table "public"."alerts" to "service_role";

grant delete on table "public"."cell_accessibility" to "anon";

grant insert on table "public"."cell_accessibility" to "anon";

grant references on table "public"."cell_accessibility" to "anon";

grant select on table "public"."cell_accessibility" to "anon";

grant trigger on table "public"."cell_accessibility" to "anon";

grant truncate on table "public"."cell_accessibility" to "anon";

grant update on table "public"."cell_accessibility" to "anon";

grant delete on table "public"."cell_accessibility" to "authenticated";

grant insert on table "public"."cell_accessibility" to "authenticated";

grant references on table "public"."cell_accessibility" to "authenticated";

grant select on table "public"."cell_accessibility" to "authenticated";

grant trigger on table "public"."cell_accessibility" to "authenticated";

grant truncate on table "public"."cell_accessibility" to "authenticated";

grant update on table "public"."cell_accessibility" to "authenticated";

grant delete on table "public"."cell_accessibility" to "service_role";

grant insert on table "public"."cell_accessibility" to "service_role";

grant references on table "public"."cell_accessibility" to "service_role";

grant select on table "public"."cell_accessibility" to "service_role";

grant trigger on table "public"."cell_accessibility" to "service_role";

grant truncate on table "public"."cell_accessibility" to "service_role";

grant update on table "public"."cell_accessibility" to "service_role";

grant delete on table "public"."grid_cells" to "anon";

grant insert on table "public"."grid_cells" to "anon";

grant references on table "public"."grid_cells" to "anon";

grant select on table "public"."grid_cells" to "anon";

grant trigger on table "public"."grid_cells" to "anon";

grant truncate on table "public"."grid_cells" to "anon";

grant update on table "public"."grid_cells" to "anon";

grant delete on table "public"."grid_cells" to "authenticated";

grant insert on table "public"."grid_cells" to "authenticated";

grant references on table "public"."grid_cells" to "authenticated";

grant select on table "public"."grid_cells" to "authenticated";

grant trigger on table "public"."grid_cells" to "authenticated";

grant truncate on table "public"."grid_cells" to "authenticated";

grant update on table "public"."grid_cells" to "authenticated";

grant delete on table "public"."grid_cells" to "service_role";

grant insert on table "public"."grid_cells" to "service_role";

grant references on table "public"."grid_cells" to "service_role";

grant select on table "public"."grid_cells" to "service_role";

grant trigger on table "public"."grid_cells" to "service_role";

grant truncate on table "public"."grid_cells" to "service_role";

grant update on table "public"."grid_cells" to "service_role";

grant delete on table "public"."hazard_predictions" to "anon";

grant insert on table "public"."hazard_predictions" to "anon";

grant references on table "public"."hazard_predictions" to "anon";

grant select on table "public"."hazard_predictions" to "anon";

grant trigger on table "public"."hazard_predictions" to "anon";

grant truncate on table "public"."hazard_predictions" to "anon";

grant update on table "public"."hazard_predictions" to "anon";

grant delete on table "public"."hazard_predictions" to "authenticated";

grant insert on table "public"."hazard_predictions" to "authenticated";

grant references on table "public"."hazard_predictions" to "authenticated";

grant select on table "public"."hazard_predictions" to "authenticated";

grant trigger on table "public"."hazard_predictions" to "authenticated";

grant truncate on table "public"."hazard_predictions" to "authenticated";

grant update on table "public"."hazard_predictions" to "authenticated";

grant delete on table "public"."hazard_predictions" to "service_role";

grant insert on table "public"."hazard_predictions" to "service_role";

grant references on table "public"."hazard_predictions" to "service_role";

grant select on table "public"."hazard_predictions" to "service_role";

grant trigger on table "public"."hazard_predictions" to "service_role";

grant truncate on table "public"."hazard_predictions" to "service_role";

grant update on table "public"."hazard_predictions" to "service_role";

grant delete on table "public"."images" to "anon";

grant insert on table "public"."images" to "anon";

grant references on table "public"."images" to "anon";

grant select on table "public"."images" to "anon";

grant trigger on table "public"."images" to "anon";

grant truncate on table "public"."images" to "anon";

grant update on table "public"."images" to "anon";

grant delete on table "public"."images" to "authenticated";

grant insert on table "public"."images" to "authenticated";

grant references on table "public"."images" to "authenticated";

grant select on table "public"."images" to "authenticated";

grant trigger on table "public"."images" to "authenticated";

grant truncate on table "public"."images" to "authenticated";

grant update on table "public"."images" to "authenticated";

grant delete on table "public"."images" to "service_role";

grant insert on table "public"."images" to "service_role";

grant references on table "public"."images" to "service_role";

grant select on table "public"."images" to "service_role";

grant trigger on table "public"."images" to "service_role";

grant truncate on table "public"."images" to "service_role";

grant update on table "public"."images" to "service_role";

grant delete on table "public"."readiness_scores" to "anon";

grant insert on table "public"."readiness_scores" to "anon";

grant references on table "public"."readiness_scores" to "anon";

grant select on table "public"."readiness_scores" to "anon";

grant trigger on table "public"."readiness_scores" to "anon";

grant truncate on table "public"."readiness_scores" to "anon";

grant update on table "public"."readiness_scores" to "anon";

grant delete on table "public"."readiness_scores" to "authenticated";

grant insert on table "public"."readiness_scores" to "authenticated";

grant references on table "public"."readiness_scores" to "authenticated";

grant select on table "public"."readiness_scores" to "authenticated";

grant trigger on table "public"."readiness_scores" to "authenticated";

grant truncate on table "public"."readiness_scores" to "authenticated";

grant update on table "public"."readiness_scores" to "authenticated";

grant delete on table "public"."readiness_scores" to "service_role";

grant insert on table "public"."readiness_scores" to "service_role";

grant references on table "public"."readiness_scores" to "service_role";

grant select on table "public"."readiness_scores" to "service_role";

grant trigger on table "public"."readiness_scores" to "service_role";

grant truncate on table "public"."readiness_scores" to "service_role";

grant update on table "public"."readiness_scores" to "service_role";

grant delete on table "public"."reports" to "anon";

grant insert on table "public"."reports" to "anon";

grant references on table "public"."reports" to "anon";

grant select on table "public"."reports" to "anon";

grant trigger on table "public"."reports" to "anon";

grant truncate on table "public"."reports" to "anon";

grant update on table "public"."reports" to "anon";

grant delete on table "public"."reports" to "authenticated";

grant insert on table "public"."reports" to "authenticated";

grant references on table "public"."reports" to "authenticated";

grant select on table "public"."reports" to "authenticated";

grant trigger on table "public"."reports" to "authenticated";

grant truncate on table "public"."reports" to "authenticated";

grant update on table "public"."reports" to "authenticated";

grant delete on table "public"."reports" to "service_role";

grant insert on table "public"."reports" to "service_role";

grant references on table "public"."reports" to "service_role";

grant select on table "public"."reports" to "service_role";

grant trigger on table "public"."reports" to "service_role";

grant truncate on table "public"."reports" to "service_role";

grant update on table "public"."reports" to "service_role";

grant delete on table "public"."roads_edges" to "anon";

grant insert on table "public"."roads_edges" to "anon";

grant references on table "public"."roads_edges" to "anon";

grant select on table "public"."roads_edges" to "anon";

grant trigger on table "public"."roads_edges" to "anon";

grant truncate on table "public"."roads_edges" to "anon";

grant update on table "public"."roads_edges" to "anon";

grant delete on table "public"."roads_edges" to "authenticated";

grant insert on table "public"."roads_edges" to "authenticated";

grant references on table "public"."roads_edges" to "authenticated";

grant select on table "public"."roads_edges" to "authenticated";

grant trigger on table "public"."roads_edges" to "authenticated";

grant truncate on table "public"."roads_edges" to "authenticated";

grant update on table "public"."roads_edges" to "authenticated";

grant delete on table "public"."roads_edges" to "service_role";

grant insert on table "public"."roads_edges" to "service_role";

grant references on table "public"."roads_edges" to "service_role";

grant select on table "public"."roads_edges" to "service_role";

grant trigger on table "public"."roads_edges" to "service_role";

grant truncate on table "public"."roads_edges" to "service_role";

grant update on table "public"."roads_edges" to "service_role";

grant delete on table "public"."shelters" to "anon";

grant insert on table "public"."shelters" to "anon";

grant references on table "public"."shelters" to "anon";

grant select on table "public"."shelters" to "anon";

grant trigger on table "public"."shelters" to "anon";

grant truncate on table "public"."shelters" to "anon";

grant update on table "public"."shelters" to "anon";

grant delete on table "public"."shelters" to "authenticated";

grant insert on table "public"."shelters" to "authenticated";

grant references on table "public"."shelters" to "authenticated";

grant select on table "public"."shelters" to "authenticated";

grant trigger on table "public"."shelters" to "authenticated";

grant truncate on table "public"."shelters" to "authenticated";

grant update on table "public"."shelters" to "authenticated";

grant delete on table "public"."shelters" to "service_role";

grant insert on table "public"."shelters" to "service_role";

grant references on table "public"."shelters" to "service_role";

grant select on table "public"."shelters" to "service_role";

grant trigger on table "public"."shelters" to "service_role";

grant truncate on table "public"."shelters" to "service_role";

grant update on table "public"."shelters" to "service_role";

grant delete on table "public"."weather_snapshots" to "anon";

grant insert on table "public"."weather_snapshots" to "anon";

grant references on table "public"."weather_snapshots" to "anon";

grant select on table "public"."weather_snapshots" to "anon";

grant trigger on table "public"."weather_snapshots" to "anon";

grant truncate on table "public"."weather_snapshots" to "anon";

grant update on table "public"."weather_snapshots" to "anon";

grant delete on table "public"."weather_snapshots" to "authenticated";

grant insert on table "public"."weather_snapshots" to "authenticated";

grant references on table "public"."weather_snapshots" to "authenticated";

grant select on table "public"."weather_snapshots" to "authenticated";

grant trigger on table "public"."weather_snapshots" to "authenticated";

grant truncate on table "public"."weather_snapshots" to "authenticated";

grant update on table "public"."weather_snapshots" to "authenticated";

grant delete on table "public"."weather_snapshots" to "service_role";

grant insert on table "public"."weather_snapshots" to "service_role";

grant references on table "public"."weather_snapshots" to "service_role";

grant select on table "public"."weather_snapshots" to "service_role";

grant trigger on table "public"."weather_snapshots" to "service_role";

grant truncate on table "public"."weather_snapshots" to "service_role";

grant update on table "public"."weather_snapshots" to "service_role";


