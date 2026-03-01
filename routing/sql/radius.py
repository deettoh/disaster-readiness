"""Implements radius-based spatial queries and verifies penalty application and resets."""

from hazard import HazardManager
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:root@localhost:5432/routing_db"

class RadiusPenaltyManager:
    """Handles spatial updates and resets for road segments within a hazard radius."""

    def __init__(self, engine):
        """Initializes with a database engine and hazard logic manager."""
        self.engine = engine
        self.hazard_manager = HazardManager()

    def reset_all_penalties(self):
        """Resets all risk penalties to zero and restores original aggregate costs."""
        reset_sql = """
            UPDATE pj_roads
            SET
                risk_penalty = 0,
                agg_cost = base_cost,
                agg_reverse_cost = CASE
                    WHEN agg_reverse_cost = -1 THEN -1
                    ELSE base_cost
                END;
        """
        with self.engine.connect() as conn:
            conn.execute(text(reset_sql))
            conn.commit()

    def apply_hazard_to_area(self, lat, lon, radius_meters, hazard_label, confidence):
        """Updates risk_penalty and agg_cost for edges within the specified radius."""
        penalty_value = self.hazard_manager.get_penalty(hazard_label, confidence)

        update_sql = """
            UPDATE pj_roads
            SET
                risk_penalty = :penalty,
                agg_cost = base_cost + :penalty,
                agg_reverse_cost = CASE
                    WHEN agg_reverse_cost = -1 THEN -1
                    ELSE (base_cost + :penalty)
                END
            WHERE ST_DWithin(
                geometry::geography,
                ST_SetSRID(ST_Point(:lon, :lat), 4326)::geography,
                :radius
            );
        """
        with self.engine.connect() as conn:
            result = conn.execute(text(update_sql), {
                "penalty": penalty_value,
                "lat": lat,
                "lon": lon,
                "radius": radius_meters
            })
            conn.commit()
            return result.rowcount

def verify_radius_task():
    """Performs a test run of the radius-based penalty implementation."""
    engine = create_engine(DATABASE_URL)
    rpm = RadiusPenaltyManager(engine)

    # Test parameters: A point in Petaling Jaya (Section 14 area)
    test_lat, test_lon = 3.110, 101.635
    test_radius = 500  # 500 meters
    hazard = "flood"
    conf = 0.9

    print("--- Affected Edges within Radius Query ---")

    # 1. Reset state
    print("Resetting existing penalties...")
    rpm.reset_all_penalties()

    # 2. Apply Hazard
    print(f"Applying '{hazard}' (conf: {conf}) within {test_radius}m of ({test_lat}, {test_lon})...")
    affected_count = rpm.apply_hazard_to_area(test_lat, test_lon, test_radius, hazard, conf)

    if affected_count > 0:
        print(f"SUCCESS: {affected_count} road segments updated with new penalties.")

        # 3. Verification Query
        verify_sql = """
            SELECT id, risk_penalty, agg_cost
            FROM pj_roads
            WHERE risk_penalty > 0
            LIMIT 5;
        """
        with engine.connect() as conn:
            rows = conn.execute(text(verify_sql)).fetchall()
            print("\nSample of affected segments (Active State):")
            for row in rows:
                print(f" - Edge ID: {row[0]} | Penalty: {row[1]} | Total Cost: {row[2]:.2f}s")

        # 4. Final Reset Verification
        print("\nVerifying Reset functionality...")
        rpm.reset_all_penalties()
        with engine.connect() as conn:
            remaining = conn.execute(text("SELECT COUNT(*) FROM pj_roads WHERE risk_penalty > 0")).scalar()
            if remaining == 0:
                print("SUCCESS: All penalties successfully reset to 0.")
            else:
                print(f"FAILURE: {remaining} penalties still exist in the database.")
    else:
        print("FAILED: No edges found within the specified radius. Check coordinates or graph data.")

if __name__ == "__main__":
    verify_radius_task()
