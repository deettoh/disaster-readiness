import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { MAPTILER_KEY } from "../api/config";
import { hazardsToGeoJSON } from "../utils/geojson";
import { mergeReadinessIntoGeoJSON } from "../utils/geojson";

const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true";
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export default function MapView({ onHazardClick }) {
  const mapContainer = useRef(null);

  useEffect(() => {
    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: `https://api.maptiler.com/maps/streets/style.json?key=${MAPTILER_KEY}`,
      center: [101.6165, 3.1292],
      zoom: 12,
    });

    return () => map.remove();  // cleanup: destroy map instance on unmount
  }, []);

  return <div ref={mapContainer} className="w-full h-full" />;
}