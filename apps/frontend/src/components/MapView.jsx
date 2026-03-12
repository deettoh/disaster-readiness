import { use, useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { MAPTILER_KEY } from "../api/config";
import { hazardsToGeoJSON } from "../utils/geojson";
import { mergeReadinessIntoGeoJSON } from "../utils/geojson";
import { shelterCSVToGeoJSON } from "../utils/geojson";
import LegendPanel from "./LegendPanel";
import { updateLayerVisibility } from "./layerController";
import * as turf from "@turf/turf";
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
  const highlightedRef = useRef(null);
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
        addRoadLayer(map, routeGeoJSON);

        const hazardGeoJSON = await loadHazards();

        addHazardLayer(map, hazardGeoJSON, (hazard) => {
          setSelectedHazard(hazard);
          onHazardClick?.(hazard);
        });

        const readinessGeoJSON = await loadReadiness();

        setLocalReadiness(readinessGeoJSON);
        setReadinessGeoJSON?.(readinessGeoJSON);
        console.log("Readiness features sent to map:", readinessGeoJSON.features.length);
        if (map.getSource("readiness")) {
          map.getSource("readiness").setData(readinessGeoJSON);
        } else {
          addReadinessLayer(map, readinessGeoJSON, onCellHover);
        }
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

    const map = mapRef.current;

    const feature = readinessGeoJSON.features.find(
      f =>
        f.properties.cell_id === zoomCell.cell ||
        f.properties.name === zoomCell.cell
    );

    if (!feature) return;

    const id = feature.properties.name;

    // remove previous alert highlight
    if (highlightedRef.current !== null) {
      map.setFeatureState(
        { source: "readiness", id: highlightedRef.current },
        { alert: false }
      );
    }

    highlightedRef.current = id;

    // set alert highlight
    map.setFeatureState(
      { source: "readiness", id },
      { alert: true }
    );

    // existing zoom
    const coords = feature.geometry.coordinates[0];
    const bounds = coords.reduce(
      (b, coord) => b.extend(coord),
      new maplibregl.LngLatBounds(coords[0], coords[0])
    );

    map.fitBounds(bounds, {
      padding: 60,
      duration: 800
    });

  }, [zoomCell]);
  // Clear alert highlight on mouse click
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const clearAlert = () => {
      if (highlightedRef.current !== null) {
        map.setFeatureState(
          { source: "readiness", id: highlightedRef.current },
          { alert: false }
        );
        highlightedRef.current = null;
      }
    };

    map.on("click", clearAlert);

    return () => {
      map.off("click", clearAlert);
    };
  }, []);

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
 * DATA LOADERS
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

/**
 * Loads neighbourhood polygons and merges with backend readiness data
 * @returns 
 */
async function loadReadiness() {
  // Load neighbourhood polygons
  const res = await fetch("/pj_neighbourhood.geojson");
  const raw = await res.json();

  // Keep only admin level 10 neighbourhood polygons (exclude OSM Point
  // nodes and higher level boundaries).
  const geojson = {
    ...raw,
    features: raw.features.filter(
      (f) =>
        (f.geometry.type === "Polygon" || f.geometry.type === "MultiPolygon") &&
        f.properties.admin_level === "10"
    ),
  };

  // Filter by admin_level == 10
  let filteredFeatures = geojson.features.filter((f) => {
    const level = Number(f.properties.admin_level);
    return !isNaN(level) && level == 10;
  });

  // Flatten MultiPolygons so each polygon piece has the same properties
  filteredFeatures = filteredFeatures.flatMap((f) => {
    if (f.geometry.type === "MultiPolygon") {
      return turf.flatten(f).features.map((piece) => {
        piece.properties = { ...f.properties }; // preserve the original props
        return piece;
      });
    }
    return f;
  });

  geojson.features = filteredFeatures;

  // Add mock readiness data if needed
  if (USE_MOCK) {
    geojson.features.forEach((feature) => {
      const score = Number((Math.random() * 100).toFixed(1));
      feature.properties.score = score;
      feature.properties.breakdown = {
        hazard_penalty: Math.random() * 50,
        vulnerability_penalty: Math.random() * 30,
        accessibility_bonus: Math.random() * 20,
        confidence_bonus: Math.random() * 10,
      };
      feature.properties.updated_at = new Date().toISOString();
    });
    return geojson;
  }

  // Backend readiness data
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
        "circle-opacity": [
          "max",
          ["get", "confidence"],
          0.4
        ],
        "circle-stroke-color": "#ffffff",
        "circle-stroke-width": 2
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
  if (map.getSource("readiness")) {
    map.getSource("readiness").setData(geojson);
    return;
  }

  map.addSource("readiness", {
    type: "geojson",
    data: geojson,
    promoteId: "name"
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
        0, "#b91c1c",
        25, "#ef4444",
        50, "#facc15",
        75, "#86efac",
        100, "#166534",
      ],
      "fill-opacity": [
        "interpolate",
        ["linear"],
        ["get", "score"],
        0, 0.35,
        100, 0.65,
      ],
    },
  });

  map.addLayer({
    id: "readiness-border",
    type: "line",
    source: "readiness",
    paint: {
      "line-color": [
        "case",
        ["boolean", ["feature-state", "alert"], false],
        "#ff0000",      // alert highlight
        ["boolean", ["feature-state", "hover"], false],
        "#ffffff",      // hover highlight
        "#000000"
      ],

      "line-width": [
        "case",
        ["boolean", ["feature-state", "alert"], false],
        6,
        ["boolean", ["feature-state", "hover"], false],
        5,
        0.5
      ],

      "line-opacity": [
        "case",
        ["boolean", ["feature-state", "alert"], false],
        0.9,
        ["boolean", ["feature-state", "hover"], false],
        0.9,
        0.4
      ]
    }
  });
  let hoveredId = null;
  map.on("mousemove", "readiness-layer", (e) => {

    if (!e.features?.length) return;

    const feature = e.features[0];
    const id = feature.id;

    if (hoveredId !== null) {
      map.setFeatureState(
        { source: "readiness", id: hoveredId },
        { hover: false }
      );
    }

    hoveredId = id;

    map.setFeatureState(
      { source: "readiness", id: hoveredId },
      { hover: true }
    );

    onCellHover?.(feature);

  });

  map.on("mouseleave", "readiness-layer", () => {
    if (hoveredId !== null) {
      map.setFeatureState(
        { source: "readiness", id: hoveredId },
        { hover: false }
      );
    }

    hoveredId = null;

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
        "circle-radius": 10,
        "circle-color": "#9900ff",      // blue fill
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
