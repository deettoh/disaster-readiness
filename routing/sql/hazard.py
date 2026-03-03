"""Define penalty mapping based on hazard type and penalty scaling based on confidence score."""
from apps.api.src.app.core.config import get_settings
from sqlalchemy import create_engine, text  # noqa: D100

# Initialize settings
settings = get_settings()

class HazardManager:
    """Manages hazard-to-penalty mapping and scaling logic."""

    def __init__(self):
        """Initializes the hazard mapping with predefined penalty values."""
        self.hazard_mapping = {
            "flood": 1200.0,
            "fire": 3600.0,
            "landslide": 5000.0,
            "normal": 0.0
        }

    def get_penalty(self, hazard_label, confidence):
        """Calculates penalty by multiplying base mapping by confidence score."""
        base_penalty = self.hazard_mapping.get(hazard_label.lower(), 0.0)
        return base_penalty * confidence

def verify_hazard_logic():
    """Verifies hazard mapping and performs a temporary database test."""
    engine = create_engine(settings.routing_database_url)
    manager = HazardManager()

    print(f"Target Environment: {settings.app_env.upper()}")
    print("--- Hazard Label Mapping ---")
    for label, val in manager.hazard_mapping.items():
        print(f"Hazard: {label.ljust(10)} | Base Penalty: {val}")

    print("\n--- Confidence Scaling Rules ---")
    test_cases = [("flood", 0.85), ("fire", 0.50), ("landslide", 0.90)]
    for label, conf in test_cases:
        p = manager.get_penalty(label, conf)
        print(f"Label: {label.ljust(10)} | Conf: {conf} | Scaled: {p}")

    print("\n--- Database Integration Test (Temporary) ---")

    with engine.connect() as conn:
        # Start a transaction manually to allow rollback
        trans = conn.begin()
        try:
            # Fetch an existing edge
            edge = conn.execute(text("SELECT id, risk_penalty FROM pj_roads LIMIT 1;")).fetchone()

            if not edge:
                print("Error: No data found in pj_roads.")
                trans.rollback()
                return

            edge_id = edge[0]
            original_penalty = edge[1] if edge[1] is not None else 0.0

            print(f"Testing Temporary Update on Edge ID: {edge_id}")
            print(f"Original Penalty: {original_penalty}")

            # Perform the Update
            test_penalty = manager.get_penalty("flood", 0.85)
            update_sql = text("""
                UPDATE pj_roads
                SET risk_penalty = :penalty,
                    agg_cost = base_cost + :penalty
                WHERE id = :edge_id;
            """)
            conn.execute(update_sql, {"penalty": test_penalty, "edge_id": edge_id})

            # Verify the change within the transaction
            verify_res = conn.execute(
                text("SELECT risk_penalty FROM pj_roads WHERE id = :id"),
                {"id": edge_id}
            ).fetchone()

            if verify_res:
                print(f"Verification (In-Transaction): New Penalty = {verify_res[0]}")

            # Rollback to undo changes
            trans.rollback()
            print("Rollback performed.")

            # Final check to prove data is reverted
            final_res = conn.execute(
                text("SELECT risk_penalty FROM pj_roads WHERE id = :id"),
                {"id": edge_id}
            ).fetchone()

            if final_res:
                print(f"Final Database State for Edge {edge_id}: Risk Penalty = {final_res[0]}")
            else:
                print("Warning: Could not re-verify edge after rollback.")

        except Exception as e:
            trans.rollback()
            print(f"Test failed and rolled back. Error: {e}")

if __name__ == "__main__":
    verify_hazard_logic()
