"""Calculates base costs, initializes risk penalties, and populates aggregated cost."""

from apps.api.src.app.core.config import get_settings
from sqlalchemy import create_engine, text

settings = get_settings()

def compute_and_initialize_costs():
    """Calculates travel times, initializes risk penalties, and totals aggregate costs."""
    engine = create_engine(settings.routing_database_url)

    # Schema setup
    setup_sql = """
        ALTER TABLE pj_roads ADD COLUMN IF NOT EXISTS base_cost DOUBLE PRECISION;
        ALTER TABLE pj_roads ADD COLUMN IF NOT EXISTS risk_penalty DOUBLE PRECISION DEFAULT 0;
        ALTER TABLE pj_roads ADD COLUMN IF NOT EXISTS agg_cost DOUBLE PRECISION;
        ALTER TABLE pj_roads ADD COLUMN IF NOT EXISTS agg_reverse_cost DOUBLE PRECISION;
    """

    # Compute base cost (Speed converted from km/h to m/s)
    base_cost_sql = """
        UPDATE pj_roads
        SET base_cost = COALESCE(length / (
            CASE
                WHEN maxspeed ~ '^[0-9]+' THEN (substring(maxspeed from '^[0-9]+')::numeric * 1000 / 3600)
                ELSE 13.88
            END
        ), length / 13.88);
    """

    # Initialize risk penalty
    risk_init_sql = """
        UPDATE pj_roads
        SET risk_penalty = 0
        WHERE risk_penalty IS NULL;
    """

    # Populate aggregated cost
    # 'agg_reverse_cost = -1' tells pgRouting a road is one-way
    agg_cost_sql = """
        UPDATE pj_roads
        SET
            agg_cost = base_cost + risk_penalty,
            agg_reverse_cost = CASE
                WHEN oneway IN ('yes', 'true', '1') THEN -1
                ELSE (base_cost + risk_penalty)
            END;
    """

    with engine.connect() as conn:
        try:
            print(f"--- {settings.app_name}: Cost & Risk Initialization ---")
            print(f"Target Environment: {settings.app_env.upper()}")

            conn.execute(text(setup_sql))
            conn.execute(text(base_cost_sql))
            conn.execute(text(risk_init_sql))
            conn.execute(text(agg_cost_sql))
            conn.commit()

            # --- Verification ---
            check_res = conn.execute(
                text("SELECT COUNT(*) FROM pj_roads WHERE agg_cost IS NULL;")
            ).fetchone()
            null_count = check_res[0] if check_res else 0

            if null_count == 0:
                print("SUCCESS: All routing costs and penalties initialized.")

                stats_query = """
                    SELECT
                        AVG(base_cost),
                        AVG(risk_penalty),
                        AVG(agg_cost)
                    FROM pj_roads;
                """
                stats_res = conn.execute(text(stats_query)).fetchone()

                if stats_res:
                    print("\nPetaling Jaya Network Stats:")
                    print(f" - Avg Travel Time (Base): {round(float(stats_res[0] or 0), 2)}s")
                    print(f" - Avg Risk Penalty:       {round(float(stats_res[1] or 0), 2)}")
                    print(f" - Avg Total Cost (Agg):    {round(float(stats_res[2] or 0), 2)}s")
            else:
                print(f"WARNING: Found {null_count} segments with missing cost data.")

        except Exception as e:
            conn.rollback()
            print(f"ERROR: Cost calculation failed: {e}")

if __name__ == "__main__":
    compute_and_initialize_costs()
