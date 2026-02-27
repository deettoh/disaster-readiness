import osmnx as ox
import os

def download_pj_road_graph():
    """Extracts PJ road data, saves it as a Shapefile, and plots the graph."""

    # Define the MVP area
    place_name = "Petaling Jaya, Selangor, Malaysia"
    
    print(f"Starting extraction for: {place_name}...")
    
    # Download the 'drive' network (filters for drivable roads)
    graph = ox.graph_from_place(place_name, network_type='drive')
    
    # Project the graph 
    graph_projected = ox.project_graph(graph)
    
    # Convert to GeoDataFrames (Nodes and Edges)
    nodes, edges = ox.graph_to_gdfs(graph_projected)
    
    # Save the data
    output_folder = "pj_mvp_data"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        
    edges.to_file(f"{output_folder}/pj_roads.shp")
    print(f"Success! Road graph saved to ./{output_folder}/pj_roads.shp")
    print(f"Stats: {len(nodes)} nodes and {len(edges)} road segments extracted.")
    ox.plot_graph(graph)
    
if __name__ == "__main__":
    download_pj_road_graph()
    
