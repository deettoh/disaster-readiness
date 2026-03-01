"""Verifies that routing paths change or update their metrics after a hazard event."""

from contract import get_route
from radius import RadiusPenaltyManager
from sqlalchemy import create_engine
from updater import HazardUpdater

DATABASE_URL = "postgresql://postgres:root@localhost:5432/routing_db"

class RouteHazardVerifier:
    """Handles the comparison of routes before and after hazard application."""

    def __init__(self):
        """Initializes database connection and managers."""
        self.engine = create_engine(DATABASE_URL)
        self.rpm = RadiusPenaltyManager(self.engine)
        self.updater = HazardUpdater()

    def verify_route_change(self, start_coords, end_coords, hazard_coords, hazard_type):
        """Calculates a baseline route, applies a hazard, and verifies the change.

        Args:
            start_coords (tuple): (lat, lon) for start.
            end_coords (tuple): (lat, lon) for end.
            hazard_coords (tuple): (lat, lon) for hazard center.
            hazard_type (str): Type of hazard to apply.
        """
        # Clear existing penalties to ensure a clean baseline
        self.rpm.reset_all_penalties()

        # Get Baseline Route
        print("--- Calculating Baseline Route ---")
        baseline = get_route(
            start_coords[0], start_coords[1],
            end_coords[0], end_coords[1]
        )

        if baseline["status"] == "error":
            print(f"Baseline Error: {baseline.get('message', 'Unknown error')}")
            return

        # Explicitly cast to float to prevent operator unsupported errors
        base_time = float(baseline.get("eta_minutes", 0.0))
        print(f"Baseline ETA: {base_time} minutes")

        # Apply Hazard (e.g., Landslide with 1.0 confidence for maximum impact)
        print(f"\n--- Simulating {hazard_type.upper()} event ---")
        self.updater.apply_hazard_event(
            hazard_coords[0], hazard_coords[1],
            radius=600,
            hazard_label=hazard_type,
            confidence=1.0
        )

        # Get Hazard-Aware Route
        print("\n--- Calculating Risk-Aware Route ---")
        post_hazard = get_route(
            start_coords[0], start_coords[1],
            end_coords[0], end_coords[1]
        )

        if post_hazard["status"] == "error":
            print(f"Post-Hazard Error: {post_hazard.get('message', 'Unknown error')}")
            return

        # Explicitly cast to float to ensure mathematical subtraction works
        hazard_time = float(post_hazard.get("eta_minutes", 0.0))
        print(f"Post-Hazard ETA: {hazard_time} minutes")

        # Analysis
        print("\n--- Final Verification Analysis ---")
        time_diff = hazard_time - base_time

        if hazard_time > base_time:
            print("SUCCESS: Route metrics updated.")
            print(f"Impact: Travel time increased by {round(time_diff, 2)} minutes.")
            print("The routing engine successfully accounted for the hazard penalty.")
        elif hazard_time == base_time:
            print("OBSERVATION: Travel time remained identical.")
            print("The hazard may not be on the primary path or the penalty was insufficient.")
        else:
            print("WARNING: Post-hazard route is faster. Check cost calculation logic.")

        # Cleanup
        self.rpm.reset_all_penalties()

def run_route_change_verification():
    """Executes the full test suite for C3 Task 6."""
    verifier = RouteHazardVerifier()

    # Test Locations: Mutiara Damansara to PJ State
    # Hazard: Placed in Section 14 (likely intersection)
    MD_START = (3.155, 101.609)
    PJS_END = (3.100, 101.645)
    HAZARD_LOC = (3.110, 101.635)

    verifier.verify_route_change(
        start_coords=MD_START,
        end_coords=PJS_END,
        hazard_coords=HAZARD_LOC,
        hazard_type="landslide"
    )

if __name__ == "__main__":
    run_route_change_verification()
