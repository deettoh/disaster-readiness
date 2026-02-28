import { useRef, useEffect } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { MAPTILER_KEY } from "../../../api/config";

export default function PinDropMapSelector({
  onLocationSelect,
  open,
  location
}) {

  const mapContainer = useRef(null);
  const mapRef = useRef(null);
  const markerRef = useRef(null);

  /** Initialize map when modal opens, only once
   * 
   */
  useEffect(() => {

    if (!open) return;
    if (mapRef.current) return;

    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: `https://api.maptiler.com/maps/streets/style.json?key=${MAPTILER_KEY}`,
      center: [101.6165, 3.1292],
      zoom: 11
    });

    mapRef.current = map;

    map.on("load", () => {
      map.resize();
    });

    /** Map click handler for pin drop
     * 
     */
    map.on("click", (e) => {

      const { lng, lat } = e.lngLat;

      if (markerRef.current) {
        markerRef.current.remove();
      }

      markerRef.current = new maplibregl.Marker()
        .setLngLat([lng, lat])
        .addTo(map);

      onLocationSelect({
        longitude: lng,
        latitude: lat
      });

    });

  }, [open]);

  
  /** Fly to location when auto-detected or when user clicks on map to select pin
   * 
   */
  useEffect(() => {

    const map = mapRef.current;

    if (!map || !location) return;

    const { longitude, latitude } = location;

    map.flyTo({
      center: [longitude, latitude],
      zoom: 15,
      essential: true
    });

    if (markerRef.current) {
      markerRef.current.remove();
    }

    markerRef.current = new maplibregl.Marker()
      .setLngLat([longitude, latitude])
      .addTo(map);

  }, [location]);

  return (
    <div className="w-full h-64 border-2 border-dashed rounded-lg overflow-hidden text-gray-500">
      <div ref={mapContainer} className="w-full h-full" />
    </div>
  );
}