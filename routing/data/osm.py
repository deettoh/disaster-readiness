import osmnx as ox
import os

def download_pj_road_graph():
    # 1. Define the MVP area
    place_name = "Petaling Jaya, Selangor, Malaysia"
    
    print(f" Starting extraction for: {place_name}...")
    
    # 2. Download the 'drive' network (filters for drivable roads)
    graph = ox.graph_from_place(place_name, network_type='drive')
    
    # 3. Project the graph 
    graph_projected = ox.project_graph(graph)
    
    # 4. Convert to GeoDataFrames (Nodes and Edges)
    nodes, edges = ox.graph_to_gdfs(graph_projected)
    
    # 5. Save the data
    output_folder = "pj_mvp_data"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        
    edges.to_file(f"{output_folder}/pj_roads.shp")
    print(f"Success! Road graph saved to ./{output_folder}/pj_roads.shp")
    print(f"Stats: {len(nodes)} nodes and {len(edges)} road segments extracted.")
    ox.plot_graph(graph)
    
if __name__ == "__main__":
    download_pj_road_graph()
    
