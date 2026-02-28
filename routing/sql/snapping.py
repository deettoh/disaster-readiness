"""Provides geometric 'snapping' logic for start points and end points."""

import random

from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:root@localhost:5432/routing_db"


def get_nearest_node(engine, lon, lat, label="Point"):
    """Snaps coordinates to the closest road node ID."""
    query = """
        SELECT
            id,
            ST_X(the_geom) as lon,
            ST_Y(the_geom) as lat,
            ST_Distance(the_geom::geography, ST_SetSRID(ST_Point(:lon, :lat), 4326)::geography) as dist_meters
        FROM pj_roads_vertices_pgr
        ORDER BY the_geom <-> ST_SetSRID(ST_Point(:lon, :lat), 4326)
        LIMIT 1;
    """

    with engine.connect() as conn:
        result = conn.execute(text(query), {"lon": lon, "lat": lat}).fetchone()

        if result:
            node_id, n_lon, n_lat, dist = result
            print(f"{label} ({lat:.6f}, {lon:.6f}) snapped to Node {node_id}")
            print(f"Distance: {round(dist, 2)} meters away.")
            return node_id
        return None


def verify_snapping_tasks():
    """Picks nodes, adds a random offset, and verifies snapping and routing."""
    engine = create_engine(DATABASE_URL)

    print("--- Route Query Engine (Random Snapping Verification) ---")

    # Fetch random coordinates from existing nodes
    random_coords_query = "SELECT ST_X(the_geom), ST_Y(the_geom) FROM pj_roads_vertices_pgr ORDER BY random() LIMIT 2;"

    with engine.connect() as conn:
        coords = conn.execute(text(random_coords_query)).fetchall()

    if len(coords) < 2:
        return

    # Add a small random offset (approx 50-100 meters) to simulate real-world input
    def jitter(val):
        return val + random.uniform(-0.0005, 0.0005)

    start_lon, start_lat = jitter(coords[0][0]), jitter(coords[0][1])
    shelter_lon, shelter_lat = jitter(coords[1][0]), jitter(coords[1][1])

    # Start Point Snapping
    start_node = get_nearest_node(engine, start_lon, start_lat, "Start Point")

    print("-" * 30)

    # End Point/Shelter Snapping
    end_node = get_nearest_node(engine, shelter_lon, shelter_lat, "Shelter/End Point")

    # Final Verification
    if start_node and end_node:
        print("\nVerification: Snapping IDs are valid for routing.")
        routing_test = """
            SELECT count(*)
            FROM pgr_dijkstra(
                'SELECT id, source, target, agg_cost AS cost FROM pj_roads',
                :start, :end, directed := true
            );
        """
        with engine.connect() as conn:
            res = conn.execute(
                text(routing_test), {"start": start_node, "end": end_node}
            ).fetchone()
            if res and res[0] > 0:
                print(
                    f"Success! A path exists between snapped nodes {start_node} and {end_node}."
                )
            else:
                print("Snapping worked, but no path exists between these points.")


if __name__ == "__main__":
    verify_snapping_tasks()
