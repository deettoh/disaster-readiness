from sqlalchemy import create_engine, text

# --- CONFIGURATION ---
DATABASE_URL = "postgresql://postgres:root@localhost:5432/routing_db"

def get_nearest_node(engine, lon, lat, label="Point"):
    """
    Finds the closest vertex ID in the road network for a given lon, lat.
    Uses the <-> operator for index-assisted nearest neighbor search.
    """
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
            print(f"{label} ({lat}, {lon}) snapped to Node {node_id}")
            print(f"Distance: {round(dist, 2)} meters away.")
            return node_id
        else:
            print(f"Could not find a nearby node for {label}.")
            return None

# Verification
def verify_c2_tasks():
    engine = create_engine(DATABASE_URL)
    
    print("--- C2: Route Query Engine (Snapping Verification) ---")
    
    # Start Point Snapping (Example: A point in Mutiara Damansara)
    start_lon, start_lat = 101.609, 3.155 
    start_node = get_nearest_node(engine, start_lon, start_lat, "Start Point")
    
    print("-" * 30)
    
    # End Point/Shelter Snapping (Example: A point near PJ State)
    shelter_lon, shelter_lat = 101.645, 3.100
    end_node = get_nearest_node(engine, shelter_lon, shelter_lat, "Shelter/End Point")
    
    # Final Verification: Can we route between them?
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
            res = conn.execute(text(routing_test), {"start": start_node, "end": end_node}).fetchone()
            if res and res[0] > 0:
                print(f"Success! A path exists between snapped nodes {start_node} and {end_node}.")
            else:
                print("Snapping worked, but no path exists between these specific points.")

if __name__ == "__main__":
    verify_c2_tasks()