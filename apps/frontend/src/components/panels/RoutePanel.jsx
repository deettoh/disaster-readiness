import { useState } from "react";
import { getRoute } from "../../api/route";

export default function RoutePanel({
  origin,
  shelters = [],
  selectedShelter,
  setSelectedShelter,
  setOrigin,
  onDrawRoute,
  onClearRoute
}) {

  const [useNearest, setUseNearest] = useState(false);
  const [routeSummary, setRouteSummary] = useState(null);

  const handleUseMyLocation = () => {
    if (!navigator.geolocation) {
      alert("Geolocation not supported in this browser.");
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const lat = pos.coords.latitude;
        const lng = pos.coords.longitude;

        setOrigin?.([lng, lat]);
      },
      (err) => {
        console.error(err);
        alert("Unable to retrieve your location.");
      }
    );
  };
  const handleCompute = async () => {

    if (!origin) {
      alert("Click on the map to select a start location.");
      return;
    }

    const params = {
      origin_lat: origin[1],
      origin_lng: origin[0]
    };

    if (useNearest) {
      params.shelter_id = "nearest";
    } else if (selectedShelter) {
      params.shelter_id = selectedShelter;
    }

    try {
      const data = await getRoute(params);

      setRouteSummary({
        distance: data.distance_meters,
        eta: data.eta_minutes
      });

      onDrawRoute?.(data.route_geojson);

    } catch (err) {
      console.error("Route error:", err);
    }
  };

  const handleClear = () => {

    setRouteSummary(null);
    setUseNearest(false);

    // Clear map related state via parent
    setOrigin?.(null);
    setSelectedShelter?.("");

    onClearRoute?.();
  };

  return (
    <div className="space-y-4 text-sm">

      <h2 className="font-semibold text-base">Evacuation Route</h2>

      <div className="space-y-1">
        
        <div className="flex items-center justify-between">

          <label className="text-xs text-gray-500">
            Start Location (click map)
          </label>

          <button
            onClick={handleUseMyLocation}
            className="text-xs text-blue-600 hover:underline"
          >
            Use my location
          </button>

        </div>

        <div className="border rounded p-2 text-xs bg-gray-50">

          {origin ? (
            <>
              <div>Lat: {origin?.[1]?.toFixed(5)}</div>
              <div>Lng: {origin?.[0]?.toFixed(5)}</div>
            </>
          ) : (
            <div className="text-gray-400">
              No origin selected
            </div>
          )}

        </div>

      </div>

      <div className="space-y-1">
        <label className="text-xs text-gray-500">Shelter</label>

        <select
          disabled={useNearest}
          value={selectedShelter || ""}
          onChange={(e) => setSelectedShelter?.(e.target.value)}
          className="border p-1 rounded w-full"
        >
          <option value="">Select Shelter</option>

          {shelters.map((s, i) => (
            <option
              key={i}
              value={s.properties?.shelter_id}
            >
              {s.properties?.name || "Shelter"}
            </option>
          ))}

        </select>

        <label className="flex items-center gap-2 text-xs">
          <input
            type="checkbox"
            checked={useNearest}
            onChange={() => {
              const next = !useNearest;
              setUseNearest(next);

              if (next && origin && shelters.length > 0) {

                let nearest = null;
                let minDist = Infinity;

                shelters.forEach(s => {

                  const [lng, lat] = s.geometry.coordinates;

                  const dist = haversineDistance(
                    origin[1],
                    origin[0],
                    lat,
                    lng
                  );

                  if (dist < minDist) {
                    minDist = dist;
                    nearest = s.properties.shelter_id;
                  }
                });

                if (nearest) {
                  setSelectedShelter?.(nearest);
                }
              }
            }}
          />
          Use nearest shelter
        </label>
      </div>

      <button
        onClick={handleCompute}
        className="bg-red-500 text-white w-full py-2 rounded"
      >
        Compute Route
      </button>

      {routeSummary && (
        <div className="bg-gray-100 p-3 rounded text-xs space-y-1">
          <p>
            Distance: {routeSummary.distance
              ? (routeSummary.distance / 1000).toFixed(2)
              : "--"} km
          </p>
          <p>
            ETA: {routeSummary.eta
              ? routeSummary.eta.toFixed(1)
              : "--"} minutes
          </p>
        </div>
      )}

      <button
        onClick={handleClear}
        className="border w-full py-2 rounded"
      >
        Clear Route
      </button>
    </div>
  );
}

/**
 * Calculates the Haversine distance between two lat/lng points in kilometers.
 * @param {*} lat1 
 * @param {*} lng1 
 * @param {*} lat2 
 * @param {*} lng2 
 * @returns 
 */
function haversineDistance(lat1, lng1, lat2, lng2) {
  const R = 6371; // Earth radius km

  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLng = (lng2 - lng1) * Math.PI / 180;

  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(lat1 * Math.PI / 180) *
    Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLng / 2) ** 2;

  return 2 * R * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}