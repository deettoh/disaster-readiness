import geopandas as gpd
from sqlalchemy import create_engine
import matplotlib.pyplot as plt

# --- 1. CONFIGURATION ---
DB_USER = "postgres"
DB_PASS = "root"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "routing_db"

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def visualize_full_map():
    # Create the connection
    engine = create_engine(DATABASE_URL)

    print(f"🔗 Connecting to {DB_NAME}...")
    
    # 2. Pull the data from PostGIS
    # We select the geometry and the highway type for better styling
    query = "SELECT geometry, highway FROM pj_roads"
    
    print("🛰️  Loading road geometries into memory...")
    gdf = gpd.read_postgis(query, engine, geom_col='geometry')

    print(f"✅ Loaded {len(gdf)} road segments.")

    # 3. Create the Visualization
    fig, ax = plt.subplots(figsize=(12, 12))
    
    print("🎨 Rendering map...")
    
    # Style the map based on road types
    # Primary roads = Thick & Dark
    # Residential = Thin & Light
    gdf.plot(
        ax=ax,
        column='highway',  # Color by road type
        legend=True,
        linewidth=0.5,
        alpha=0.8,
        cmap='tab20b'      # Nice color palette for different road classes
    )

    # 4. Final Formatting
    ax.set_title("Full Road Network Extraction: Petaling Jaya", fontsize=15)
    ax.set_axis_off()  # Hide latitude/longitude coordinates for a cleaner look
    
    # Save the result
    output_file = "pj_full_map_visualization.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    
    print(f"💾 Visualization saved as: {output_file}")
    plt.show()

if __name__ == "__main__":
    try:
        visualize_full_map()
    except Exception as e:
        print(f"❌ Error during visualization: {e}")