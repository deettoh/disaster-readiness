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

        # Initialize Penalty Manager (this one usually takes the engine)
        self.rpm = RadiusPenaltyManager(self.engine)

        # FIXED: Initialize HazardUpdater without arguments to satisfy the "0 positional" rule
        self.updater = HazardUpdater()

        # If HazardUpdater needs the engine to work, it often looks for a setter:
        # self.updater.engine = self.engine

    def verify_route_change(self, start_coords, end_coords, hazard_coords, hazard_type):
        """Calculates a baseline route, applies a hazard, and verifies the change."""
        # Clear existing penalties to ensure a clean baseline
        self.rpm.reset_all_penalties()

        # Get Baseline Route
        print("--- Calculating Baseline Route ---")
        baseline = get_route(
            start_coords[0], start_coords[1],
            end_coords[0], end_coords[1],
            engine=self.engine # Required keyword argument
        )

        if baseline.get("status") == "error":
            print(f"Baseline Error: {baseline.get('message', 'Unknown error')}")
            return

        base_time = float(baseline.get("eta_minutes", 0.0))
        print(f"Baseline ETA: {base_time} minutes")

        # Apply Hazard
        print(f"\n--- Simulating {hazard_type.upper()} event ---")
        # NOTE: If apply_hazard_event throws an 'engine' error here,
        # pass it as: self.updater.apply_hazard_event(..., engine=self.engine)
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
            end_coords[0], end_coords[1],
            engine=self.engine # Required keyword argument
        )

        if post_hazard.get("status") == "error":
            print(f"Post-Hazard Error: {post_hazard.get('message', 'Unknown error')}")
            return

        hazard_time = float(post_hazard.get("eta_minutes", 0.0))
        print(f"Post-Hazard ETA: {hazard_time} minutes")

        # Analysis
        print("\n--- Final Verification Analysis ---")
        time_diff = hazard_time - base_time

        if hazard_time > base_time:
            print("SUCCESS: Route metrics updated.")
            print(f"Impact: Travel time increased by {round(time_diff, 2)} minutes.")
        elif hazard_time == base_time:
            print("OBSERVATION: Travel time identical. Hazard might be off-path.")
        else:
            print("WARNING: Post-hazard route is faster. Check cost logic.")

        # Cleanup
        self.rpm.reset_all_penalties()

def run_route_change_verification():
    """Executes the full test suite."""
    verifier = RouteHazardVerifier()

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
