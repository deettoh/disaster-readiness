"""Prepare a shelter location file."""

import osmnx as ox
import pandas as pd
import warnings

# Ignore the CRS warning for centroids
warnings.filterwarnings("ignore", category=UserWarning)

def download_safe_shelters():
    """Downloads PJ community centers likely used for flood/disaster relief."""
    
    place_name = "Petaling Jaya, Selangor, Malaysia"
    
    # Refined tags: Community centers and halls are the standard 'safe' zones in PJ
    # We remove 'place_of_worship' to prioritize government-vetted facilities
    tags: dict[str, str | bool | list[str]] = {
        'amenity': ['community_centre', 'townhall'],
        'building': 'civic'
    }
    
    print(f"Fetching safe evacuation centers for {place_name}...")
    
    try:
        # Get features from OSM
        shelters = ox.features_from_place(place_name, tags)
        
        # Project to meters for accurate center point calculation
        shelters_proj = ox.projection.project_gdf(shelters)
        points = shelters_proj.centroid.to_crs(epsg=4326)
        
        # Extract names and coordinates
        if 'name' in shelters.columns:
            names = shelters['name'].fillna("Dewan Komuniti (Unspecified)")
        else:
            names = ["Dewan Komuniti"] * len(shelters)
        
        df = pd.DataFrame({
            'name': names,
            'lon': points.x,
            'lat': points.y
        })

        # Safety Filter: Prioritize "Dewan" or "Pusat Komuniti" 
        df = df[df['name'].str.contains('Dewan|Pusat|Komuniti|Hall', case=False, na=False)]
        
        df = df.head(5).reset_index(drop=True)
        
        # Export and Print
        df.to_csv("pj_shelters.csv", index_label="shelter_id")
        
        print(f"\nSuccessfully saved {len(df)} SAFE shelters to 'pj_shelters.csv':")
        print("-" * 60)
        print(df[['name', 'lon', 'lat']].to_string())
        print("-" * 60)
        
    except Exception as e:
        print(f"Error fetching shelters: {e}")

if __name__ == "__main__":
    download_safe_shelters()