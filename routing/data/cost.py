from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:root@localhost:5432/routing_db"

def compute_and_initialize_costs():
    """ Calculates travel times (base_cost), initializes risk penalties to 0, and totals them into an aggregate cost column. """
    
    engine = create_engine(DATABASE_URL)
    
    # SCHEMA SETUP 
    setup_sql = """
        ALTER TABLE pj_roads ADD COLUMN IF NOT EXISTS base_cost DOUBLE PRECISION;
        ALTER TABLE pj_roads ADD COLUMN IF NOT EXISTS risk_penalty DOUBLE PRECISION DEFAULT 0;
        ALTER TABLE pj_roads ADD COLUMN IF NOT EXISTS agg_cost DOUBLE PRECISION;
        ALTER TABLE pj_roads ADD COLUMN IF NOT EXISTS agg_reverse_cost DOUBLE PRECISION;
    """
    
    # COMPUTE BASE COST 
    base_cost_sql = """
        UPDATE pj_roads
        SET base_cost = COALESCE(length / (
            CASE 
                WHEN maxspeed ~ '^[0-9]+' THEN (substring(maxspeed from '^[0-9]+')::numeric * 1000 / 3600)
                ELSE 13.88 -- Default 50km/h
            END
        ), length / 13.88);
    """

    # INITIALIZE RISK PENALTY
    risk_init_sql = """
        UPDATE pj_roads 
        SET risk_penalty = 0 
        WHERE risk_penalty IS NULL;
    """

    # POPULATE AGGREGATED COST
    agg_cost_sql = """
        UPDATE pj_roads 
        SET 
            agg_cost = base_cost + risk_penalty,
            agg_reverse_cost = CASE 
                WHEN oneway IN ('yes', 'true', '1') THEN -1 
                ELSE (base_cost + risk_penalty) 
            END;
    """

    # INDEXING
    index_sql = """
        CREATE INDEX IF NOT EXISTS pj_roads_source_idx ON pj_roads (source);
        CREATE INDEX IF NOT EXISTS pj_roads_target_idx ON pj_roads (target);
    """

    with engine.connect() as conn:
        try:
            print("--- Executing Task 5 & 6: Cost Calculation ---")
            conn.execute(text(setup_sql))
            conn.execute(text(base_cost_sql))
            conn.execute(text(risk_init_sql))
            conn.execute(text(agg_cost_sql))
            conn.execute(text(index_sql))
            conn.commit()
            
            # --- SAFE VERIFICATION ---
            check_res = conn.execute(text("SELECT COUNT(*) FROM pj_roads WHERE agg_cost IS NULL;")).fetchone()
            null_count = check_res[0] if check_res else 0

            if null_count == 0:
                print("SUCCESS: All costs and penalties initialized.")
                
                stats_res = conn.execute(text("""
                    SELECT 
                        AVG(base_cost), 
                        AVG(risk_penalty), 
                        AVG(agg_cost) 
                    FROM pj_roads;
                """)).fetchone()

                if stats_res:
                    avg_base = stats_res[0] if stats_res[0] is not None else 0
                    avg_risk = stats_res[1] if stats_res[1] is not None else 0
                    avg_total = stats_res[2] if stats_res[2] is not None else 0

                    print(f"\nStats Report:")
                    print(f" - Avg Base Cost: {round(float(avg_base), 2)}s")
                    print(f" - Avg Risk Penalty: {round(float(avg_risk), 2)}")
                    print(f" - Avg Total Cost: {round(float(avg_total), 2)}s")
            else:
                print(f"Warning: Found {null_count} rows with NULL costs.")

        except Exception as e:
            conn.rollback()
            print(f"Error during execution: {e}")

if __name__ == "__main__":
    compute_and_initialize_costs()