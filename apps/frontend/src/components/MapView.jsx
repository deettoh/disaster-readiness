import { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { MAPTILER_KEY } from "../api/config";
import { hazardsToGeoJSON } from "../utils/geojson";
import { mergeReadinessIntoGeoJSON } from "../utils/geojson";
import { shelterCSVToGeoJSON } from "../utils/geojson";
import LegendPanel from "./LegendPanel";
import { updateLayerVisibility } from "./layerController";
const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true";
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;



export default function MapView({
  onHazardClick,
  onCellHover,
  setReadinessGeoJSON,
  zoomCell,
  shelters,
  origin,
  setOrigin,
  routeGeoJSON,
  selectedShelter,
  activePanel,
  layers,
  toggleLayer
}) {
  const mapContainer = useRef(null);
  const mapRef = useRef(null);

  const [selectedHazard, setSelectedHazard] = useState(null);
  const [readinessGeoJSON, setLocalReadiness] = useState(null);
  const activePanelRef = useRef(activePanel);

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
        const roadRes = await fetch("/data/pj_routes.geojson");
        const roadGeoJSON = await roadRes.json();
        addRoadLayer(map, roadGeoJSON);

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
      map.on("click", (e) => {
        if(activePanelRef.current !== "route") return;
        const { lng, lat } = e.lngLat;
        setOrigin([lng, lat]);

      });
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

  const originMarkerRef = useRef(null);

  useEffect(() => {
    if (!mapRef.current) return;
    if (!mapRef.current.isStyleLoaded()) return;

    if (!origin) {
      if (originMarkerRef.current) {
        originMarkerRef.current.remove();
        originMarkerRef.current = null;
      }
      return;
    }

    if (originMarkerRef.current) {
      originMarkerRef.current.remove();
    }

    const el = document.createElement("div");
    el.innerHTML = `
    <svg width="30" height="30" viewBox="0 0 24 24" fill="red">
      <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/>
    </svg>
    `;

    originMarkerRef.current = new maplibregl.Marker(el)
      .setLngLat(origin)
      .addTo(mapRef.current);

  }, [origin]);
  
  useEffect(() => {

    if (!mapRef.current || !routeGeoJSON) return;
    if (!mapRef.current.isStyleLoaded()) return;

    if (mapRef.current.getSource("evac-route")) {
      mapRef.current.getSource("evac-route").setData(routeGeoJSON);
      return;
    }

    mapRef.current.addSource("evac-route", {
      type: "geojson",
      data: routeGeoJSON
    });

    mapRef.current.addLayer({
      id: "evac-route",
      type: "line",
      source: "evac-route",
      paint: {
        "line-width": 5,
        "line-color": "#2563eb"
      }
    });

  }, [routeGeoJSON]);

  useEffect(() => {
    if (!mapRef.current || shelters.length === 0) return;
    if (!mapRef.current.isStyleLoaded()) return;

    const geojson = { type: "FeatureCollection", features: shelters };

    if (!mapRef.current.getSource("shelters")) {
      mapRef.current.addSource("shelters", { type: "geojson", data: geojson });
      mapRef.current.addLayer({
        id: "shelters",
        type: "circle",
        source: "shelters",
        paint: {
          "circle-radius": [
            "case",
            ["==", ["get", "shelter_id"], selectedShelter],
            11,
            6
          ],
          "circle-color": [
            "case",
            ["==", ["get", "shelter_id"], selectedShelter],
            "#22c55e",
            "#3b82f6"
          ],
          "circle-stroke-width": [
            "case",
            ["==", ["get", "shelter_id"], selectedShelter],
            3,
            1
          ],
          "circle-stroke-color": "#ffffff"
        }
      });
    } else {
      mapRef.current.getSource("shelters").setData(geojson);
      mapRef.current.setPaintProperty("shelters", "circle-radius", [
        "case",
        ["==", ["get", "shelter_id"], selectedShelter],
        11,
        6
      ]);
      mapRef.current.setPaintProperty("shelters", "circle-color", [
        "case",
        ["==", ["get", "shelter_id"], selectedShelter],
        "#22c55e",
        "#3b82f6"
      ]);
      mapRef.current.setPaintProperty("shelters", "circle-stroke-width", [
        "case",
        ["==", ["get", "shelter_id"], selectedShelter],
        3,
        1
      ]);
    }
  }, [shelters, selectedShelter]);

  useEffect(() => {
    activePanelRef.current = activePanel;
  }, [activePanel]);

  useEffect(() => {
    if (!mapRef.current || !selectedShelter) return;

    const shelter = shelters.find(
      s => s.properties.shelter_id === selectedShelter
    );

    if (!shelter) return;

    const [lng, lat] = shelter.geometry.coordinates;

    mapRef.current.flyTo({
      center: [101.6165, 3.1292],
      zoom: 11,
      duration: 800
    });

  }, [selectedShelter]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    if (!map.isStyleLoaded()) return;

    updateLayerVisibility(map, layers);

  }, [layers]);

  return (
    <div className="relative w-full h-full">
      <div ref={mapContainer} className="w-full h-full" />
      <LegendPanel 
        layers={layers}
        toggleLayer={toggleLayer}
      />
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

  const hazardTypes = [
    { id: "flood", color: "#2563eb" },
    { id: "fire", color: "#dc2626" },
    { id: "landslide", color: "#f59e0b" },
    { id: "normal", color: "#00ff48" }
  ];

  hazardTypes.forEach((hazard) => {

    map.addLayer({
      id: `hazards-${hazard.id}`,
      type: "circle",
      source: "hazards",
      filter: ["==", ["get", "label"], hazard.id],
      paint: {
        "circle-radius": 7,
        "circle-color": hazard.color,
        "circle-opacity": ["get", "confidence"],
      }
    });

    // click event
    map.on("click", `hazards-${hazard.id}`, (e) => {

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

  });

  // Hover popup (works for all layers)
  const hoverPopup = new maplibregl.Popup({
    closeButton: false,
    closeOnClick: false,
  });

  hazardTypes.forEach((hazard) => {

    map.on("mouseenter", `hazards-${hazard.id}`, (e) => {

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

    map.on("mouseleave", `hazards-${hazard.id}`, () => {

      map.getCanvas().style.cursor = "";
      hoverPopup.remove();
    });

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

function addRoadLayer(map, geojson) {

  if (!map.getSource("pj-roads-source")) {
    map.addSource("pj-roads-source", {
      type: "geojson",
      data: geojson
    });
  } else {
    map.getSource("pj-roads-source").setData(geojson);
  }

  if (map.getLayer("pj-roads-shadow")) {
    map.removeLayer("pj-roads-shadow");
  }

  if (map.getLayer("pj-roads")) {
    map.removeLayer("pj-roads");
  }

  map.addLayer({
    id: "pj-roads-shadow",
    type: "line",
    source: "pj-roads-source",
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
      "line-opacity": 0.25,
      "line-blur": 1.5
    }
  });

  map.addLayer({
    id: "pj-roads",
    type: "line",
    source: "pj-roads-source",
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
      "line-opacity": 0.5
    }
  });

}

/**
 * Draws a route on the map
 * @param {*} map 
 * @param {*} geojson 
 */
export function drawRoute(map, geojson) {

  if (!map.getSource("evac-route")) {
    map.addSource("evac-route", {
      type: "geojson",
      data: geojson
    });

    map.addLayer({
      id: "evac-route",
      type: "line",
      source: "evac-route",
      paint: {
        "line-color": "#2563eb",
        "line-width": 6
      }
    });

  } else {
    map.getSource("evac-route").setData(geojson);
  }

}
/**
 * Clears the route from the map
 * @param {*} map 
 * @returns 
 */
export function clearRoute(map) {

  if (!map) return;

  if (map.getLayer("evac-route")) {
    map.removeLayer("evac-route");
  }

  if (map.getSource("evac-route")) {
    map.removeSource("evac-route");
  }

}