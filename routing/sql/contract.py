from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Tuple

# --- INPUT CONTRACT ---
# This defines exactly what Member A must send to the routing engine.
class RouteRequest(BaseModel):
    # Field(...) indicates a required field. 
    # 'examples' provides metadata for documentation (FastAPI/Swagger).
    start_coords: Tuple[float, float] = Field(
        ..., 
        examples=[(101.609, 3.155)],
        description="Longitude and Latitude of the starting point"
    )
    end_coords: Tuple[float, float] = Field(
        ..., 
        examples=[(101.645, 3.100)],
        description="Longitude and Latitude of the destination"
    )
    algorithm: str = Field(
        default="dijkstra", 
        description="The pathfinding algorithm to use: 'dijkstra' or 'astar'"
    )

    @field_validator('start_coords', 'end_coords')
    @classmethod
    def validate_malaysia_bounds(cls, v: Tuple[float, float]) -> Tuple[float, float]:
        lon, lat = v
        # Bounding box for the Petaling Jaya extract
        if not (101.0 <= lon <= 102.0 and 2.5 <= lat <= 4.0):
            raise ValueError("Coordinates are outside the supported Petaling Jaya region")
        return v

# --- OUTPUT CONTRACT ---
# This defines the "promise" of what Member C returns to Member A.
class RouteMetrics(BaseModel):
    distance_km: float
    eta_minutes: float
    segment_count: int

class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    geometry: dict  # Should contain a LineString
    properties: dict

class RouteResponse(BaseModel):
    status: str = Field(..., examples=["success"])
    message: Optional[str] = None
    data: Optional[RouteMetrics] = None
    geojson: Optional[GeoJSONFeature] = None

# --- ERROR CONTRACT ---
# Edge cases (Out of bounds, No path, etc.)
class RouteError(BaseModel):
    status: str = "error"
    error_code: str  
    message: str

if __name__ == "__main__":
    # Internal test to verify the contract logic
    try:
        # Test 1: Valid request
        valid_req = RouteRequest(
            start_coords=(101.609, 3.155),
            end_coords=(101.615, 3.160)
        )
        print("Contract Validation Success: Valid coordinates accepted.")
        
        # Test 2: Invalid request (Out of bounds)
        print("Testing Out of Bounds (London)...")
        invalid_req = RouteRequest(
            start_coords=(-0.127, 51.507), 
            end_coords=(101.645, 3.100)
        )
    except ValueError as e:
        print(f"Contract Validation Success: Caught expected error: {e}")