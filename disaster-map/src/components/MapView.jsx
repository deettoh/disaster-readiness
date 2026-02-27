import { useEffect, useRef } from "react";
import { MAPTILER_KEY } from "../api/config";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
/**
 * MapView component initializes and renders the map using MapLibre GL JS.
 */

export default function MapView() {
  const mapContainer = useRef(null);

  useEffect(() => {
    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: `https://api.maptiler.com/maps/streets/style.json?key=${MAPTILER_KEY}`,
      center: [101.6165, 3.1292],
      zoom: 12,
    });

    return () => map.remove();  
  }, []);

  return <div ref={mapContainer} className="w-full h-full" />;
}