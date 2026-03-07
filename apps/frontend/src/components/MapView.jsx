import { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { MAPTILER_KEY } from "../api/config";
import { hazardsToGeoJSON } from "../utils/geojson";
import { mergeReadinessIntoGeoJSON } from "../utils/geojson";
import { shelterCSVToGeoJSON } from "../utils/geojson";
import LegendPanel from "./LegendPanel";
const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true";
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;



export default function MapView({
  onHazardClick,
  onCellHover,
  setReadinessGeoJSON,
  zoomCell
}) {
  const mapContainer = useRef(null);
  const mapRef = useRef(null);

  const [selectedHazard, setSelectedHazard] = useState(null);
  const [readinessGeoJSON, setLocalReadiness] = useState(null);

  // Map loading and layer initialization
  useEffect(() => {
    if (mapRef.current) return;

    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: `https://api.maptiler.com/maps/streets/style.json?key=${MAPTILER_KEY}`,
      center: [101.6165, 3.1292],
      zoom: 12,
    });

    mapRef.current = map;

    map.on("load", async () => {
      try {
        const routeRes = await fetch("/pj_routes.geojson");
        const routeGeoJSON = await routeRes.json();
        addRouteLayer(map, routeGeoJSON);

        const readinessGeoJSON = await loadReadiness();

        setLocalReadiness(readinessGeoJSON); 
        setReadinessGeoJSON?.(readinessGeoJSON);

        addReadinessLayer(map, readinessGeoJSON, onCellHover);

        const hazardGeoJSON = await loadHazards();

        addHazardLayer(map, hazardGeoJSON, (hazard) => {
          setSelectedHazard(hazard);
          onHazardClick?.(hazard);
        });

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

  // Zoom to cell when triggered by alert click
  useEffect(() => {
    if (!zoomCell?.cell || !mapRef.current || !readinessGeoJSON) return;

    const feature = readinessGeoJSON.features.find(
      f =>
        f.properties.cell_id === zoomCell.cell ||
        f.properties.name === zoomCell.cell
    );

    if (!feature || !feature.geometry) return;

    try {
      const coords = feature.geometry.coordinates[0];

      const bounds = coords.reduce(
        (b, coord) => b.extend(coord),
        new maplibregl.LngLatBounds(coords[0], coords[0])
      );

      mapRef.current.fitBounds(bounds, {
        padding: 60,
        duration: 800
      });

    } catch (err) {
      console.error("Zoom cell fitBounds failed:", err);
    }
  }, [zoomCell]);

  return (
    <div className="relative w-full h-full">
      <div ref={mapContainer} className="w-full h-full" />
      <LegendPanel />
    </div>
  );
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

    geojson.features.forEach((feature) => {

      const score = Number((Math.random() * 100).toFixed(1));

      feature.properties.score = score;

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

  map.on("click", "hazards-layer", (e) => {

  if (!e.features?.length) return;

  const feature = e.features[0];

  const hazardData = {
    report_id: feature.properties.report_id,
    confidence: feature.properties.confidence,
    label: feature.properties.label,
    redacted_image_url: feature.properties.image,
    observed_at: feature.properties.observed_at
  };

  onHazardClick?.(hazardData);

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

function addReadinessLayer(map, geojson, onCellHover) {
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
  map.on("mousemove", "readiness-layer", (e) => {

  if (!e.features?.length) {
    onCellHover?.(null);
    return;
  }

  onCellHover?.(e.features[0]);

});

// Reset when mouse leaves polygon
map.on("mouseleave", "readiness-layer", () => {
  onCellHover?.(null);
});
}

async function addShelterLayer(map) {

  const geojson = await shelterCSVToGeoJSON("/pj_shelters.csv");

  if (!map.getSource("shelter-source")) {
    map.addSource("shelter-source", {
      type: "geojson",
      data: geojson
    });
  } else {
    map.getSource("shelter-source").setData(geojson);
  }

  if (!map.getLayer("shelter-layer")) {

    map.addLayer({
      id: "shelter-layer",
      type: "circle",
      source: "shelter-source",
      paint: {
        "circle-radius": 7,
        "circle-color": "#3b82f6",      // blue fill
        "circle-stroke-color": "#ffffff", // white outer border
        "circle-stroke-width": 2
      }
    });

  }

  map.off("click", "shelter-layer", shelterPopupHandler);
  map.on("click", "shelter-layer", shelterPopupHandler);
}

function shelterPopupHandler(e) {

  if (!e.features || !e.features.length) return;

  const props = e.features[0].properties;

  new maplibregl.Popup()
    .setLngLat(e.lngLat)
    .setHTML(`
      <strong>Shelter</strong><br/>
      ${props.name ?? "Unknown shelter"}
    `)
    .addTo(e.target);
}

function addRouteLayer(map, geojson) {

  if (!map.getSource("route-source")) {
    map.addSource("route-source", {
      type: "geojson",
      data: geojson
    });
  } else {
    map.getSource("route-source").setData(geojson);
  }

  /* Remove existing layers first (important) */
  if (map.getLayer("route-shadow-layer")) {
    map.removeLayer("route-shadow-layer");
  }

  if (map.getLayer("route-layer")) {
    map.removeLayer("route-layer");
  }

  /* Shadow layer */
  map.addLayer({
    id: "route-shadow-layer",
    type: "line",
    source: "route-source",
    layout: {
      "line-cap": "round",
      "line-join": "round"
    },
    paint: {
      "line-color": "#1e40af",
      "line-width": [
        "interpolate",
        ["linear"],
        ["zoom"],
        10, 2,
        14, 4,
        18, 6
      ],
      "line-opacity": 0.35,
      "line-blur": 1.5
    }
  });

  /* Main route layer */
  map.addLayer({
    id: "route-layer",
    type: "line",
    source: "route-source",
    layout: {
      "line-cap": "round",
      "line-join": "round"
    },
    paint: {
      "line-color": "#5773a0",
      "line-width": [
        "interpolate",
        ["linear"],
        ["zoom"],
        10, 1.5,
        14, 2.5,
        18, 4
      ],
      "line-opacity": 0.7
    }
  });
}