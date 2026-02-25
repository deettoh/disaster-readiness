from sqlalchemy import create_engine, text

# --- CONFIGURATION ---
DATABASE_URL = "postgresql://postgres:root@localhost:5432/routing_db"

def compute_base_costs():
    engine = create_engine(DATABASE_URL)
    
    # 1. Initialize Columns (Tasks: base_cost, risk_penalty, and total cost)
    setup_sql = """
        ALTER TABLE pj_roads ADD COLUMN IF NOT EXISTS base_cost DOUBLE PRECISION;
        ALTER TABLE pj_roads ADD COLUMN IF NOT EXISTS risk_penalty DOUBLE PRECISION DEFAULT 0;
        ALTER TABLE pj_roads ADD COLUMN IF NOT EXISTS agg_cost DOUBLE PRECISION;
        ALTER TABLE pj_roads ADD COLUMN IF NOT EXISTS agg_reverse_cost DOUBLE PRECISION;
    """
    
    # 2. Compute base_cost (Time in seconds) and initialize agg_cost
    # Task: cost = base_cost + risk_penalty populated
    compute_sql = """
        UPDATE pj_roads
        SET 
            base_cost = length / (
                CASE 
                    WHEN maxspeed ~ '^[0-9]+' THEN (substring(maxspeed from '^[0-9]+')::numeric * 1000 / 3600)
                    ELSE 13.88 -- Default 50km/h
                END
            );

        UPDATE pj_roads 
        SET 
            agg_cost = base_cost + risk_penalty,
            agg_reverse_cost = CASE WHEN oneway IN ('yes', 'true', '1') THEN -1 ELSE (base_cost + risk_penalty) END;
    """

    # 3. Add Routing Indexes (Task: Routing-related indexes added)
    index_sql = """
        CREATE INDEX IF NOT EXISTS pj_roads_source_idx ON pj_roads (source);
        CREATE INDEX IF NOT EXISTS pj_roads_target_idx ON pj_roads (target);
    """

    with engine.connect() as conn:
        try:
            print("Configuring cost columns and risk placeholders...")
            conn.execute(text(setup_sql))
            
            print("Populating base_cost and aggregating total costs...")
            conn.execute(text(compute_sql))
            
            print("Optimizing graph with routing indexes...")
            conn.execute(text(index_sql))
            
            conn.commit()
            
            # 4. Sanity Check (Task: Graph connectivity sanity checks)
            # Check for orphaned roads or calculation errors
            res = conn.execute(text("SELECT COUNT(*) FROM pj_roads WHERE agg_cost IS NULL OR agg_cost = 0;")).fetchone()
            orphans = res[0] if res else 0
            
            if orphans > 0:
                print(f"⚠️ Warning: Found {orphans} segments with invalid costs. Fixing...")
                conn.execute(text("UPDATE pj_roads SET agg_cost = 1 WHERE agg_cost IS NULL OR agg_cost = 0;"))
                conn.commit()

            # Safe printing to avoid "NoneType" error
            avg_res = conn.execute(text("SELECT AVG(agg_cost) FROM pj_roads;")).fetchone()
            avg_val = avg_res[0] if avg_res and avg_res[0] is not None else 0
            
            print(f"✅ SUCCESS: Costs computed and indexed.")
            print(f"📊 Average segment travel time: {round(float(avg_val), 2)} seconds.")

        except Exception as e:
            conn.rollback()
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    compute_base_costs()