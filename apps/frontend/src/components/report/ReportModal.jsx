import { useState, useEffect } from "react";
import PinDropMapSelector from "./map/PinDropMapSelector";
export default function ReportModal({ open, onClose }) {

  const [stage, setStage] = useState(1);

  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);

  const [location, setLocation] = useState(null);
  const [detectingLocation, setDetectingLocation] = useState(false);

  /**
   * Detect location only in Stage 2
   */
  useEffect(() => {
    if (open && stage === 2) {
      detectLocation();
    }
  }, [open, stage]);

  if (!open) return null;

  /** Image selection handler
   * 
   * @param {*} e 
   * @returns 
   */
  function handleImageChange(e) {
    const file = e.target.files[0];
    if (!file) return;

    setImageFile(file);
    setImagePreview(URL.createObjectURL(file));
  }

  /** GPS Location detection using browser Geolocation API
   * 
   * @returns 
   */
  function detectLocation() {

    if (!navigator.geolocation) {
        alert("Geolocation not supported");
        return;
    }

    setDetectingLocation(true);

    navigator.geolocation.getCurrentPosition(
        (position) => {

        const lng = position.coords.longitude;
        const lat = position.coords.latitude;

        const newLocation = {
            longitude: lng,
            latitude: lat,
            autoDetected: true
        };

        setLocation(newLocation);

        setDetectingLocation(false);

        },
        (error) => {

        console.log(error);
        alert("Location permission denied or unavailable");

        setDetectingLocation(false);

        },
        {
        enableHighAccuracy: true,
        timeout: 15000
        }
    );
}

  /** Render Stage 1 - Photo Upload
   * 
   * @returns 
   */
  function renderPhotoStage() {
    return (
      <>
        <div className="border-2 border-dashed rounded-lg p-6 text-center text-sm text-gray-500">

          {!imagePreview ? (
            <label className="cursor-pointer">
              Tap to take or upload photo
              <input
                type="file"
                accept="image/*"
                onChange={handleImageChange}
                className="hidden"
              />
            </label>
          ) : (
            <div className="space-y-3">
              <img
                src={imagePreview}
                alt="Preview"
                className="w-full rounded-lg"
              />

              <button
                onClick={() => {
                  setImageFile(null);
                  setImagePreview(null);
                }}
                className="w-full text-sm border rounded-lg py-2"
              >
                Retake Photo
              </button>
            </div>
          )}

        </div>

        <div className="flex justify-end gap-2 pt-2">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm border rounded-lg"
          >
            Cancel
          </button>

          <button
            disabled={!imageFile}
            onClick={() => setStage(2)}
            className={`px-4 py-2 text-sm rounded-lg text-white ${
              imageFile
                ? "bg-red-600 hover:bg-red-700"
                : "bg-gray-400 cursor-not-allowed"
            }`}
          >
            Continue
          </button>
        </div>
      </>
    );
  }

  /**Render Stage 2 - Location Selection
   * 
   * @returns 
   */
  function renderLocationStage() {
    return (
        <div className="space-y-1">

        <h3 className="text-sm font-semibold">
            Select Location
        </h3>

        <button
            onClick={detectLocation}
            className="w-full bg-red-600 text-white py-2 rounded-lg text-sm"
        >
            Detect Location 
        </button>

        <p className="text-xs text-gray-400 text-center">
            OR drop pin manually
        </p>

        <PinDropMapSelector open={stage === 2} location={location}onLocationSelect={setLocation} />

        {location && (
            <div className="text-center text-sm">
            <p>Selected Location:</p>
            <p>
                {location.latitude.toFixed(6)}, 
                {location.longitude.toFixed(6)}
            </p>
            </div>
        )}

        <div className="flex justify-end gap-2 pt-2">

            <button
            onClick={() => setStage(1)}
            className="px-4 py-2 border rounded-lg text-sm"
            >
            Back
            </button>

            <button
            disabled={!location}
            className={`px-4 py-2 text-sm rounded-lg text-white ${
                location
                ? "bg-red-600 hover:bg-red-700"
                : "bg-gray-400 cursor-not-allowed"
            }`}
            >
            Continue
            </button>

        </div>

        </div>
    );
}

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">

     <div className="bg-white w-full max-w-md max-h-[85vh] rounded-2xl shadow-xl flex flex-col overflow-hidden">
        <div className="p-6 space-y-4 overflow-y-auto flex-1">
            <h2 className="text-lg font-semibold">
                Report Hazard
            </h2>

            <p className="text-sm text-gray-600">
                Upload photo and allow location access to submit hazard report.
            </p>

            {stage === 1 && renderPhotoStage()}
            {stage === 2 && renderLocationStage()}
        </div>
      </div>
    </div>
  );
}