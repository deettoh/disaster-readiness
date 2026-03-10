export function updateLayerVisibility(map, layers) {

  if (!map) return;

  const visibility = (state) => state ? "visible" : "none";

  /* Hazards (individual layers) */

  if (map.getLayer("hazards-flood")) {
    map.setLayoutProperty(
      "hazards-flood",
      "visibility",
      visibility(layers.flood)
    );
  }

  if (map.getLayer("hazards-fire")) {
    map.setLayoutProperty(
      "hazards-fire",
      "visibility",
      visibility(layers.fire)
    );
  }

  if (map.getLayer("hazards-landslide")) {
    map.setLayoutProperty(
      "hazards-landslide",
      "visibility",
      visibility(layers.landslide)
    );
  }

  if (map.getLayer("hazards-normal")) {
    map.setLayoutProperty(
      "hazards-normal",
      "visibility",
      visibility(layers.normal)
    );
  }


  /* Readiness */

  const filters = [];

  if (layers.lowReadiness) {
    filters.push(["<", ["get", "score"], 40]);
  }

  if (layers.mediumReadiness) {
    filters.push([
      "all",
      [">=", ["get", "score"], 40],
      ["<=", ["get", "score"], 69],
    ]);
  }

  if (layers.highReadiness) {
    filters.push([">=", ["get", "score"], 70]);
  }

  if (filters.length === 0) {
    map.setLayoutProperty("readiness-layer", "visibility", "none");
    map.setLayoutProperty("readiness-border", "visibility", "none");
  } else {
    map.setLayoutProperty("readiness-layer", "visibility", "visible");
    map.setLayoutProperty("readiness-border", "visibility", "visible");

    map.setFilter("readiness-layer", ["any", ...filters]);
    map.setFilter("readiness-border", ["any", ...filters]);
  }


  /* Shelter */

  if (map.getLayer("shelter-layer")) {
    map.setLayoutProperty(
      "shelter-layer",
      "visibility",
      visibility(layers.shelter)
    );
  }


  /* Roads / Routes */

  if (map.getLayer("pj-roads")) {
    map.setLayoutProperty(
      "pj-roads",
      "visibility",
      visibility(layers.route)
    );
  }

  if (map.getLayer("pj-roads-shadow")) {
    map.setLayoutProperty(
      "pj-roads-shadow",
      "visibility",
      visibility(layers.route)
    );
  }

}