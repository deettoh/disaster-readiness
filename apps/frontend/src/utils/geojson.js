import Papa from "papaparse";
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
  readinessItems
) {
  if (!geojson?.features || !Array.isArray(readinessItems)) {
    return geojson;
  }

  const readinessMap = new Map();

  readinessItems.forEach(item => {
    readinessMap.set(item.cell_id, item);
  });

  geojson.features.forEach(feature => {

    const polygonName =
      feature.properties.name?.trim();

    const readinessData =
      readinessMap.get(polygonName);

    feature.properties.score =
      readinessData?.score ?? 0;

    feature.properties.breakdown =
      readinessData?.breakdown ?? {
        hazard_penalty: 0,
        vulnerability_penalty: 0,
        accessibility_bonus: 0,
        confidence_bonus: 0
      };

    feature.properties.updated_at =
      readinessData?.updated_at ?? null;

  });

  return geojson;
}
/**
 *  Convert shelter CSV data to GeoJSON format for MapLibre
 * @param {*} csvPath 
 * @returns 
 */
export async function shelterCSVToGeoJSON(csvPath) {

  const response = await fetch(csvPath);
  const csvText = await response.text();

  const parsed = Papa.parse(csvText, {
    header: true,
    skipEmptyLines: true
  });

  const features = parsed.data.map(row => ({
    type: "Feature",
    properties: {
      shelter_id: row.shelter_id,
      name: row.name
    },
    geometry: {
      type: "Point",
      coordinates: [
        parseFloat(row.lon),
        parseFloat(row.lat)
      ]
    }
  }));

  return {
    type: "FeatureCollection",
    features
  };
}