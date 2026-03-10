"""Import processed road data directly into roads_edges table."""

import os
import re
import sys
from io import StringIO

import psycopg2
from dotenv import load_dotenv

from app.core.config import get_settings  # noqa: E402

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(ROOT_DIR)
sys.path.append(os.path.join(ROOT_DIR, "apps", "api", "src"))

load_dotenv(os.path.join(ROOT_DIR, ".env"))

SQL_FILE = os.path.join(ROOT_DIR, "routing/artifacts/pj_processed_roads.sql")


def import_data():
    """Import processed road data into canonical roads_edges table."""
    settings = get_settings()
    conn_string = settings.database_url

    if not os.path.exists(SQL_FILE):
        print(f"Error: File not found at {SQL_FILE}")
        return

    conn = psycopg2.connect(conn_string)
    cur = conn.cursor()

    try:
        cur.execute("SET search_path TO public, extensions;")

        # -- Step 1: Import the dump into a TEMP staging table ---
        # Drop any lingering staging objects from a previous run
        print("Preparing staging area...")
        for obj in ["_staging_roads", "_staging_vertices", "topology_stats_summary"]:
            for cmd in ["DROP MATERIALIZED VIEW", "DROP VIEW", "DROP TABLE"]:
                try:
                    cur.execute(f"{cmd} IF EXISTS public.{obj} CASCADE;")
                    conn.commit()
                except psycopg2.Error:
                    conn.rollback()

        print("Reading and patching SQL file...")
        with open(SQL_FILE, encoding="utf-8") as f:
            full_content = f.read()

        # --- Patching logic ---
        # 1. Remove psql meta-commands (e.g. \restrict)
        full_content = re.sub(r"^\\(?!\.).*$", "", full_content, flags=re.MULTILINE)

        # 2. Rename dump tables to staging names so they don't conflict
        #    with the canonical VIEW/MATVIEW of the same name.
        full_content = full_content.replace(
            "public.pj_roads_vertices_pgr", "public._staging_vertices"
        )
        full_content = full_content.replace("public.pj_roads", "public._staging_roads")

        # 3. Basic cleanup for Supabase compatibility
        full_content = re.sub(
            r"SELECT pg_catalog\.set_config\('search_path'.*?\);", "", full_content
        )
        full_content = re.sub(r"CREATE EXTENSION IF NOT EXISTS.*?;", "", full_content)
        full_content = re.sub(r"COMMENT ON EXTENSION.*?;", "", full_content)
        full_content = full_content.replace("public.geometry", "extensions.geometry")
        full_content = full_content.replace(
            "public.spatial_ref_sys", "extensions.spatial_ref_sys"
        )

        # --- Execute the patched SQL ---
        parts = re.split(r"(COPY .*? FROM stdin;)", full_content, flags=re.IGNORECASE)

        for i in range(len(parts)):
            part = parts[i].strip()
            if not part:
                continue

            if part.upper().startswith("COPY"):
                copy_query = part
                if i + 1 < len(parts):
                    data_block = parts[i + 1].split(r"\.", 1)
                    data_part = data_block[0].strip()

                    if "spatial_ref_sys" in copy_query.lower():
                        print("Skipping system table spatial_ref_sys...")
                    else:
                        print(f"Streaming data: {copy_query[:60]}...")
                        cur.copy_expert(copy_query, StringIO(data_part + "\n"))

                    if len(data_block) > 1:
                        parts[i + 1] = data_block[1]
                continue

            elif i > 0 and parts[i - 1].upper().startswith("COPY"):
                continue

            else:
                # Strip all comments before splitting by semicolon
                part = re.sub(r"/\*.*?\*/", "", part, flags=re.DOTALL)
                cleaned_lines = []
                for line in part.splitlines():
                    clean_line = re.sub(r"--.*$", "", line).strip()
                    if clean_line:
                        cleaned_lines.append(clean_line)
                part_content = " ".join(cleaned_lines)

                for stmt in part_content.split(";"):
                    clean_stmt = stmt.strip()
                    if not clean_stmt:
                        continue

                    lower_stmt = clean_stmt.lower()
                    skip_kw = ["spatial_ref_sys", "postgis", "pgrouting"]
                    if any(kw in lower_stmt for kw in skip_kw) and (
                        lower_stmt.startswith("insert")
                        or lower_stmt.startswith("create")
                        or lower_stmt.startswith("comment")
                        or lower_stmt.startswith("set")
                    ):
                        continue

                    try:
                        cur.execute(clean_stmt)
                    except psycopg2.Error as e:
                        print(f"Error near: {clean_stmt[:150]}...")
                        raise e

        # -- Step 2: Sync staging data into canonical roads_edges --
        print("Syncing staging data into roads_edges...")
        cur.execute("""
            TRUNCATE TABLE public.roads_edges;

            INSERT INTO public.roads_edges (
                geom, source, target, cost, reverse_cost, length, base_cost
            )
            SELECT
                geometry,
                u::bigint,
                v::bigint,
                cost,
                cost,
                length,
                base_cost
            FROM public._staging_roads;
        """)

        # -- Step 3: Refresh the materialized view --
        print("Refreshing pj_roads_vertices_pgr materialized view...")
        cur.execute("REFRESH MATERIALIZED VIEW public.pj_roads_vertices_pgr;")

        # -- Step 4: Clean up staging tables --
        print("Cleaning up staging tables...")
        cur.execute("DROP TABLE IF EXISTS public._staging_roads CASCADE;")
        cur.execute("DROP TABLE IF EXISTS public._staging_vertices CASCADE;")
        cur.execute("DROP TABLE IF EXISTS public.topology_stats_summary CASCADE;")

        conn.commit()
        print("Success: Road data imported and roads_edges table updated.")

    except Exception as e:
        print(f"Failed: {e}")
        conn.rollback()

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    import_data()
