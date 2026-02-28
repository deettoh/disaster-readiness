"""Implements radius-based spatial queries and tracks a specific edge for detailed state verification."""

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
            conn.execute(text(update_sql), {
                "penalty": penalty_value,
                "lat": lat,
                "lon": lon,
                "radius": radius_meters
            })
            conn.commit()
            return penalty_value

    def get_edge_state(self, lat, lon):
        """Finds the nearest edge to a point and returns its current cost metrics."""
        query = """
            SELECT id, base_cost, risk_penalty, agg_cost
            FROM pj_roads
            ORDER BY geometry <-> ST_SetSRID(ST_Point(:lon, :lat), 4326)
            LIMIT 1;
        """
        with self.engine.connect() as conn:
            return conn.execute(text(query), {"lat": lat, "lon": lon}).fetchone()

def run_detailed_verification():
    """Executes a 3-phase verification tracking a single edge for proof of calculation and reset."""
    engine = create_engine(DATABASE_URL)
    rpm = RadiusPenaltyManager(engine)

    # Test coordinates (Section 14, PJ)
    t_lat, t_lon = 3.110, 101.635
    t_radius = 300
    t_hazard = "fire"
    t_conf = 1.0

    print("--- DETAILED EDGE STATE VERIFICATION ---")

    # PHASE 1: Initial Reset
    rpm.reset_all_penalties()
    state_init = rpm.get_edge_state(t_lat, t_lon)
    edge_id = state_init[0]

    # PHASE 2: Apply Hazard
    applied_p = rpm.apply_hazard_to_area(t_lat, t_lon, t_radius, t_hazard, t_conf)
    state_hazard = rpm.get_edge_state(t_lat, t_lon)

    # PHASE 3: Final Reset
    rpm.reset_all_penalties()
    state_final = rpm.get_edge_state(t_lat, t_lon)

    # Formatting Results
    def format_row(label, data):
        return f"{label.ljust(15)} | Penalty: {str(data[2]).ljust(8)} | Agg Cost: {str(round(data[3], 2)).ljust(10)}"

    print(f"Tracking Edge ID: {edge_id}")
    print("-" * 50)
    print(format_row("INITIAL (CLEAN)", state_init))
    print(format_row("HAZARD ACTIVE", state_hazard))
    print(format_row("POST-RESET", state_final))
    print("-" * 50)

    # Logic Check
    math_correct = state_hazard[3] == (state_hazard[1] + applied_p)
    reset_correct = state_final[2] == 0

    if math_correct and reset_correct:
        print("SUCCESS: Edge state transitions verified correctly.")
    else:
        print("FAILURE: Verification mismatch detected.")

if __name__ == "__main__":
    run_detailed_verification()
