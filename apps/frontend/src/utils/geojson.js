/** 
 * Convert API hazard response to GeoJSON format for MapLibre
 * 
 * @param {*} apiResponse 
 * @returns 
 */
export function hazardsToGeoJSON(apiResponse) {
  return {
    type: "FeatureCollection",
    features: apiResponse.items.map((item) => ({
      type: "Feature",
      properties: {
        report_id: item.report_id,
        label: item.hazard_label,
        confidence: item.confidence,
        observed_at: item.observed_at,
        image: item.redacted_image_url
      },
      geometry: {
        type: "Point",
        coordinates: [
          item.location.longitude,
          item.location.latitude
        ]
      }
    }))
  };
}

/**
 * Combine readiness scores from API with GeoJSON polygons for map visualization
 * 
 * @param {*} geojson 
 * @param {*} readinessItems 
 * @param {*} geoKey 
 * @param {*} readinessKey 
 * @returns 
 */
export function mergeReadinessIntoGeoJSON(
  geojson,
  readinessItems,
  geoKey = "name",      // property in GeoJSON
  readinessKey = "area_name" // property in API
) {
  const scoreMap = {};

  // Build lookup table
  readinessItems.forEach((item) => {
    scoreMap[item[readinessKey]] = item.score;
  });

  // Inject score into each polygon
  geojson.features.forEach((feature) => {
    const areaIdentifier = feature.properties[geoKey];

    feature.properties.score =
      scoreMap[areaIdentifier] ?? 0;

    feature.properties.updated_at =
      scoreMap[areaIdentifier] !== undefined
        ? new Date().toISOString()
        : null;
  });

  return geojson;
}
