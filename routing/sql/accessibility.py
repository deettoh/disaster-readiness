"""Implements accessibility metrics, per-cell accessibility computation and store them in table."""

from apps.api.src.app.core.config import get_settings
from sqlalchemy import create_engine, text

settings = get_settings()

class AccessibilityManager:
    """Manages the definition, computation, and storage of accessibility metrics."""

    def __init__(self):
        """Initializes the database connection."""
        self.engine = create_engine(settings.routing_database_url)

    def setup_infrastructure(self):
        """Creates the accessibility table and a mock shelters table for testing."""
        setup_sql = """
            CREATE TABLE IF NOT EXISTS shelters (
                id SERIAL PRIMARY KEY,
                node_id BIGINT,
                name TEXT,
                geometry GEOMETRY(Point, 4326)
            );

            CREATE TABLE IF NOT EXISTS cell_accessibility (
                id SERIAL PRIMARY KEY,
                cell_geom GEOMETRY(Polygon, 4326),
                center_node_id BIGINT,
                nearest_shelter_id BIGINT,
                travel_time_sec DOUBLE PRECISION,
                accessibility_score TEXT
            );

            CREATE INDEX IF NOT EXISTS cell_acc_geom_idx ON cell_accessibility USING GIST (cell_geom);
        """
        with self.engine.connect() as conn:
            conn.execute(text(setup_sql))

            check_shelters = conn.execute(text("SELECT COUNT(*) FROM shelters")).scalar()
            if check_shelters == 0:
                print("Populating mock shelters from existing road nodes...")
                pop_shelters = """
                    INSERT INTO shelters (node_id, name, geometry)
                    SELECT id, 'Shelter ' || id, the_geom
                    FROM pj_roads_vertices_pgr
                    ORDER BY RANDOM()
                    LIMIT 5;
                """
                conn.execute(text(pop_shelters))
            conn.commit()

    def compute_accessibility(self, grid_size_meters=800):
        """Generates a grid using generate_series and calculates shelter costs."""
        print(f"Computing accessibility metrics for {grid_size_meters}m grid cells...")

        # Approximate conversion from meters to degrees
        step = grid_size_meters / 111320.0

        compute_sql = f"""
            DELETE FROM cell_accessibility;

            WITH bounds AS (
                SELECT
                    ST_XMin(ST_Extent(geometry)) as x_min,
                    ST_XMax(ST_Extent(geometry)) as x_max,
                    ST_YMin(ST_Extent(geometry)) as y_min,
                    ST_YMax(ST_Extent(geometry)) as y_max
                FROM pj_roads
            ),
            -- Generate a series of X and Y coordinates to create a grid of points
            grid_points AS (
                SELECT
                    x, y
                FROM bounds,
                generate_series(bounds.x_min::numeric, bounds.x_max::numeric, {step}::numeric) as x,
                generate_series(bounds.y_min::numeric, bounds.y_max::numeric, {step}::numeric) as y
            ),
            -- Build Polygons (cells) from the generated coordinates
            grid AS (
                SELECT ST_SetSRID(ST_MakeEnvelope(x, y, x + {step}, y + {step}), 4326) as cell
                FROM grid_points
            ),
            cell_centers AS (
                SELECT
                    cell,
                    (SELECT id FROM pj_roads_vertices_pgr
                     ORDER BY the_geom <-> ST_Centroid(cell) LIMIT 1) as nearest_node
                FROM grid
                -- Optimization: only process cells that actually contain road segments
                WHERE EXISTS (SELECT 1 FROM pj_roads WHERE ST_Intersects(pj_roads.geometry, cell))
            ),
            shelter_nodes AS (
                SELECT ARRAY_AGG(node_id) as ids FROM shelters
            ),
            costs AS (
                SELECT
                    start_vid,
                    MIN(agg_cost) as min_time
                FROM pgr_dijkstraCost(
                    'SELECT id, source, target, agg_cost AS cost FROM pj_roads',
                    (SELECT ARRAY_AGG(DISTINCT nearest_node) FROM cell_centers),
                    (SELECT ids FROM shelter_nodes),
                    directed := true
                )
                GROUP BY start_vid
            )
            INSERT INTO cell_accessibility (cell_geom, center_node_id, travel_time_sec, accessibility_score)
            SELECT
                cc.cell,
                cc.nearest_node,
                co.min_time,
                CASE
                    WHEN co.min_time < 300 THEN 'Excellent'
                    WHEN co.min_time < 600 THEN 'Good'
                    WHEN co.min_time < 1200 THEN 'Fair'
                    ELSE 'Poor'
                END
            FROM cell_centers cc
            JOIN costs co ON cc.nearest_node = co.start_vid;
        """
        with self.engine.connect() as conn:
            conn.execute(text(compute_sql))
            conn.commit()

    def verify_metrics(self):
        """Performs validation on the computed accessibility data."""
        verify_sql = """
            SELECT
                COUNT(*) as total_cells,
                AVG(travel_time_sec) / 60 as avg_wait_min,
                MAX(travel_time_sec) / 60 as max_wait_min,
                COUNT(*) FILTER (WHERE accessibility_score = 'Poor') as poor_access_cells
            FROM cell_accessibility;
        """
        with self.engine.connect() as conn:
            res = conn.execute(text(verify_sql)).fetchone()
            if res and res[0] is not None and res[0] > 0:
                print("\n--- Accessibility Task Verification ---")
                print(f"Target Environment: {settings.app_env.upper()}")
                print(f"Total Cells Processed: {res[0]}")
                print(f"Average Travel Time to Shelter: {round(float(res[1]), 2)} minutes")
                print(f"Maximum Travel Time to Shelter: {round(float(res[2]), 2)} minutes")
                print(f"High-Risk Cells (Poor Access): {res[3]}")
                print("SUCCESS: cell_accessibility table populated and verified.")
            else:
                print("FAILED: No accessibility metrics were generated.")

if __name__ == "__main__":
    manager = AccessibilityManager()
    manager.setup_infrastructure()
    manager.compute_accessibility(grid_size_meters=800)
    manager.verify_metrics()
