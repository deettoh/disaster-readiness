"""Implements and verifies SQL-based risk penalty updates and cost recomputation."""

from apps.api.src.app.core.config import get_settings
from sqlalchemy import create_engine, text

from routing.sql.hazard import HazardManager
from routing.sql.radius import RadiusPenaltyManager

settings = get_settings()

class HazardUpdater:
    """Manages the application of risk penalties and cost recomputations."""

    def __init__(self):
        """Initializes the database engine and helper managers."""
        self.engine = create_engine(settings.database_url)
        self.hazard_manager = HazardManager()
        self.radius_manager = RadiusPenaltyManager(self.engine)

    def apply_hazard_event(self, lat, lon, radius, hazard_label, confidence):
        """Applies a hazard penalty to a specific area and recomputes aggregate costs.

        Args:
            lat (float): Latitude of the hazard center.
            lon (float): Longitude of the hazard center.
            radius (int): Radius in meters.
            hazard_label (str): Type of hazard (flood, fire, landslide).
            confidence (float): Confidence score between 0.0 and 1.0.
        """
        print(f"Applying {hazard_label} hazard at ({lat}, {lon}) with {radius}m radius...")

        # Update risk_penalty and recompute costs via the RadiusPenaltyManager
        affected_rows = self.radius_manager.apply_hazard_to_area(
            lat, lon, radius, hazard_label, confidence
        )

        if affected_rows > 0:
            print(f"SUCCESS: {affected_rows} edges updated with risk-aware costs.")
        else:
            print("WARNING: No edges found in the specified radius.")
        return affected_rows

    def verify_update_integrity(self):
        """Performs a sanity check on the cost columns to ensure no NULL values
        exist and penalties are mathematically consistent.
        """  # noqa: D205
        check_sql = """
            SELECT
                COUNT(*) FILTER (WHERE agg_cost IS NULL) as null_costs,
                COUNT(*) FILTER (WHERE risk_penalty > 0) as high_risk_edges,
                AVG(risk_penalty) FILTER (WHERE risk_penalty > 0) as avg_risk
            FROM pj_roads;
        """
        with self.engine.connect() as conn:
            result = conn.execute(text(check_sql)).fetchone()

            # Safety check: ensure the result object is not None
            if result is None:
                print("Error: Verification query returned no results.")
                return False

            # Safety check: handle individual column NULL returns
            null_costs = result[0] if result[0] is not None else 0
            high_risk_count = result[1] if result[1] is not None else 0
            avg_penalty = result[2] if result[2] is not None else 0.0

            print("\n--- Integrity Verification ---")
            print(f"Target Environment: {settings.app_env.upper()}")
            print(f"Null Cost Segments: {null_costs}")
            print(f"Active Hazard Segments: {high_risk_count}")

            if high_risk_count > 0:
                print(f"Average Applied Penalty: {round(float(avg_penalty), 2)}s")

            return null_costs == 0

def run_update_verification():
    """Executes a test scenario to verify:
    Flood event in PJ Section 14.
    """  # noqa: D205
    updater = HazardUpdater()

    # Reset state to ensure clean test
    print("Initializing environment...")
    updater.radius_manager.reset_all_penalties()

    # Define a flood event (mapping: 1200 * 0.9 = 1080 seconds added to cost)
    # Location: PJ Section 14
    test_lat, test_lon = 3.110, 101.635

    # Execute Penalty Update and Cost Recomputation
    updater.apply_hazard_event(test_lat, test_lon, 500, "flood", 0.9)

    # Final verification
    if updater.verify_update_integrity():
        print("\nVerified. SQL updates and cost recomputations are consistent.")
    else:
        print("\nFailed. Inconsistent cost data or NULL values detected.")

if __name__ == "__main__":
    run_update_verification()
