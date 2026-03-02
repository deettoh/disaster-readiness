import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { MAPTILER_KEY } from "../api/config";
import { hazardsToGeoJSON } from "../utils/geojson";
import { mergeReadinessIntoGeoJSON } from "../utils/geojson";
import { shelterCSVToGeoJSON } from "../utils/geojson";

const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true";
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;



export default function MapView({ onHazardClick }) {
  const mapContainer = useRef(null);
  const mapRef = useRef(null);
  useEffect(() => {
  if (mapRef.current) return; // Prevent reinitialization

  const map = new maplibregl.Map({
    container: mapContainer.current,
    style: `https://api.maptiler.com/maps/streets/style.json?key=${MAPTILER_KEY}`,
    center: [101.6165, 3.1292],
    zoom: 12,
  });

  mapRef.current = map;

  map.on("load", async () => {
    try {
      const hazardGeoJSON = await loadHazards();
      addHazardLayer(map, hazardGeoJSON, onHazardClick);

      const readinessGeoJSON = await loadReadiness();
      addReadinessLayer(map, readinessGeoJSON);

      await addShelterLayer(map);

    } catch (err) {
      console.error("Failed to initialize layers:", err);
    }
  });

  return () => {
    if (mapRef.current) {
      mapRef.current.remove();
      mapRef.current = null;
    }
  };
}, []);

  return <div ref={mapContainer} className="w-full h-full" />;
}

/*
 * DATA LODAERS
 */

async function loadHazards() {
  if (USE_MOCK) {
    console.log("Using mock hazard data");

    const mockData = {
      items: [
        {
          report_id: "1",
          hazard_label: "flood",
          confidence: 0.85,
          location: { latitude: 3.13, longitude: 101.62 },
          redacted_image_url: null,
          observed_at: new Date().toISOString(),
        },
        {
          report_id: "2",
          hazard_label: "landslide",
          confidence: 0.6,
          location: { latitude: 3.125, longitude: 101.61 },
          redacted_image_url: null,
          observed_at: new Date().toISOString(),
        },
      ],
    };

    return hazardsToGeoJSON(mockData);
  }

  console.log("Fetching hazards from API");

  const res = await fetch(`${API_BASE_URL}/hazards`);
  if (!res.ok) throw new Error("API error");

  const data = await res.json();
  return hazardsToGeoJSON(data);
}

async function loadReadiness() {
  // Load neighbourhood polygons first
  const res = await fetch("/pj_neighbourhood.geojson");
  const geojson = await res.json();

  if (USE_MOCK) {
    // Generate random readiness per polygon
    geojson.features.forEach((feature) => {
      feature.properties.score = Number(
        (Math.random() * 100).toFixed(1)
      );

      feature.properties.breakdown = {
        baseline_vulnerability: Math.random(),
        recent_hazards: Math.random(),
        accessibility: Math.random(),
        coverage_confidence: Math.random(),
      };

      feature.properties.updated_at = new Date().toISOString();
    });

    return geojson;
  }

  // When backend ready
  const apiRes = await fetch(`${API_BASE_URL}/readiness`);
  const readinessData = await apiRes.json();

  return mergeReadinessIntoGeoJSON(geojson, readinessData.items);
}

/*
 * LAYERS
 */

function addHazardLayer(map, geojson, onHazardClick) {
  map.addSource("hazards", {
    type: "geojson",
    data: geojson,
  });

  map.addLayer({
    id: "hazards-layer",
    type: "circle",
    source: "hazards",
    paint: {
      "circle-radius": 7,
      "circle-color": [
        "match",
        ["get", "label"],
        "flood", "#2563eb",
        "fire", "#dc2626",
        "landslide", "#f59e0b",
        "#00ff48"
      ],
      "circle-opacity": ["get", "confidence"],
    },
  });

  // Click → update panel
  map.on("click", "hazards-layer", (e) => {
    const props = e.features[0].properties;
    onHazardClick(props);
  });

  // Hover popup
  const hoverPopup = new maplibregl.Popup({
    closeButton: false,
    closeOnClick: false,
  });

  map.on("mouseenter", "hazards-layer", (e) => {
    map.getCanvas().style.cursor = "pointer";
    const props = e.features[0].properties;

    hoverPopup
      .setLngLat(e.lngLat)
      .setHTML(`
        <strong>${props.label}</strong><br/>
        Confidence: ${Number(props.confidence).toFixed(2)}
      `)
      .addTo(map);
  });

  map.on("mouseleave", "hazards-layer", () => {
    map.getCanvas().style.cursor = "";
    hoverPopup.remove();
  });
}

function addReadinessLayer(map, geojson) {
  map.addSource("readiness", {
    type: "geojson",
    data: geojson,
  });

  map.addLayer({
    id: "readiness-layer",
    type: "fill",
    source: "readiness",
    paint: {
      "fill-color": [
        "interpolate",
        ["linear"],
        ["get", "score"],
        0,  "#b91c1c",
        25, "#ef4444",
        50, "#facc15",
        75, "#86efac",
        100,"#166534"
      ],
      "fill-opacity": [
        "interpolate",
        ["linear"],
        ["get", "score"],
        0, 0.35,
        100, 0.65
      ]
    }
  });

  // Map subsection's border
  map.addLayer({
    id: "readiness-border",
    type: "line",
    source: "readiness",
    paint: {
      "line-color": "#000000",
      "line-width": 1,
      "line-opacity": 0.1
    }
  });
}

async function addShelterLayer(map) {

  const geojson = await shelterCSVToGeoJSON(
    "/data/shelters.csv"
  );

  map.addSource("shelter-source", {
    type: "geojson",
    data: geojson
  });

  map.addLayer({
    id: "shelter-layer",
    type: "circle",
    source: "shelter-source",
    paint: {
      "circle-radius": 8,
      "circle-color": "#0ea5e9",
      "circle-stroke-width": 2,
      "circle-stroke-color": "#ffffff"
    }
  });

  /* Popup interaction */
  map.on("click", "shelter-layer", (e) => {

    const props = e.features[0].properties;

    new maplibregl.Popup()
      .setLngLat(e.lngLat)
      .setHTML(`
        <strong>🏠 Shelter</strong><br/>
        ${props.name}
      `)
      .addTo(map);

  });

}