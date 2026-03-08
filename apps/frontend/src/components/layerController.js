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

  const readinessVisible =
    layers.highReadiness ||
    layers.mediumReadiness ||
    layers.lowReadiness;

  if (map.getLayer("readiness-layer")) {
    map.setLayoutProperty(
      "readiness-layer",
      "visibility",
      readinessVisible ? "visible" : "none"
    );
  }

  if (map.getLayer("readiness-border")) {
    map.setLayoutProperty(
      "readiness-border",
      "visibility",
      readinessVisible ? "visible" : "none"
    );
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