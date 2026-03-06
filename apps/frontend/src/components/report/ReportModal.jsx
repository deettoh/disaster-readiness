import { useState, useEffect } from "react";
import PinDropMapSelector from "./map/PinDropMapSelector";
export default function ReportModal({ open, onClose }) {

  const [stage, setStage] = useState(1);

  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);

  const [location, setLocation] = useState(null);
  const [detectingLocation, setDetectingLocation] = useState(false);
  const [hazardType, setHazardType] = useState("fire");
  const [hazardLabel, setHazardLabel] = useState("");

  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [reportId, setReportId] = useState(null);
  const [resultPopup, setResultPopup] = useState(null); 


  useEffect(() => {

    if (!processing || !reportId || !open) return;

    const interval = setInterval(async () => {

      try {

        const res = await fetch(
          `http://localhost:8000/reports/${reportId}/status`
        );

        if (!res.ok) return;

        const data = await res.json();

        if (data.status === "complete") {

          clearInterval(interval);

          setProcessing(false);
          setResultPopup("success");

          setTimeout(() => {
            resetForm();
            onClose();
            setResultPopup(null);
          }, 1500);
        }

        if (data.status === "failed") {

          clearInterval(interval);

          setProcessing(false);
          setResultPopup("failed");
        }

      } catch (err) {
        console.error(err);
      }

    }, 2000);

    return () => clearInterval(interval);

  }, [processing, reportId, open]);
  
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
        {location && (
        <div className="space-y-3 pt-3 border-t">

          {/* Hazard Type Selector */}
          <div>
            <p className="text-sm font-medium mb-2">Select a hazard type </p>
            <div className="flex gap-2">
              {["fire", "flood", "landslide"].map((type) => (
                <button
                  key={type}
                  type="button"
                  onClick={() => setHazardType(type)}
                  className={`px-3 py-1 rounded-full text-xs border transition
                    ${
                      hazardType === type
                        ? "bg-red-600 text-white border-red-600"
                        : "bg-white text-gray-700 border-gray-300 hover:bg-gray-100"
                    }`}
                >
                  {type.charAt(0).toUpperCase() + type.slice(1)}
                </button>
              ))}
            </div>
          </div>
          {/* Optional Label */}
          <div>
            <label className="text-sm font-medium">
              Additional Details (Optional)
            </label>
            <textarea
              value={hazardLabel}
              onChange={(e) => setHazardLabel(e.target.value)}
              placeholder="Add extra description..."
              className="w-full mt-1 border rounded-lg p-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-600"
            />
          </div>
        </div>
      )}
        <div className="flex justify-end gap-2 pt-2">

            <button
            onClick={() => setStage(1)}
            className="px-4 py-2 border rounded-lg text-sm"
            >
            Back
            </button>

            {/* Success / Error Messages
            {uploadError && (
              <p className="text-sm text-red-600 text-center">
                {uploadError}
              </p>
            )} */}

            {uploadSuccess && (
              <p className="text-sm text-green-600 text-center">
                Report submitted successfully!
              </p>
            )}

            <button
              disabled={!location || uploading || processing}
              onClick={handleSubmit}
              className={`px-4 py-2 text-sm rounded-lg text-white ${
                !location || uploading || processing
                  ? "bg-gray-400 cursor-not-allowed"
                  : "bg-red-600 hover:bg-red-700"
              }`}
            >
              {uploading
                ? "Uploading..."
                : processing
                ? "Processing..."
                : "Submit Report"}
            </button>

        </div>

        </div>
    );
}
/**
 * Handle final submission of the hazard report
 */
async function handleSubmit() {
  try {
    setUploading(true);
    setUploadError(null);

    // ---- Step 1: Create report metadata ----
    const createResponse = await fetch(
      "http://localhost:8000/reports",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          location,
          note: hazardLabel || "",
          user_hazard_label: hazardType,
        }),
      }
    );

    if (!createResponse.ok)
      throw new Error("Failed to create report");

    const createData = await createResponse.json();
    const newReportId = createData.report_id;

    setReportId(newReportId);

    // ---- Step 2: Upload Image ----
    const formData = new FormData();
    formData.append("image", imageFile);

    const uploadResponse = await fetch(
      `http://localhost:8000/reports/${newReportId}/image`,
      {
        method: "POST",
        body: formData,
      }
    );

    if (!uploadResponse.ok)
      throw new Error("Image upload failed");

    // ---- Step 3: Transition State ----
    setUploading(false);
    setProcessing(true);

  } catch (err) {
    setUploadError(err.message);
    setUploading(false);
  }
}

function resetForm() {
  setStage(1);
  setImageFile(null);
  setImagePreview(null);
  setLocation(null);
  setHazardType("fire");
  setHazardLabel("");
  setUploadError(null);
  setUploadSuccess(false);
}
    
  if (!open) return null;
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
        {resultPopup && (
          <div className="fixed inset-0 flex items-center justify-center bg-black/50 z-60">

            <div className="bg-white p-6 rounded-xl text-center space-y-4">

              {resultPopup === "success" && (
                <p className="text-green-600 font-semibold">
                  Report submitted successfully 🎉
                </p>
              )}

              {resultPopup === "failed" && (
                <p className="text-red-600 font-semibold">
                  Processing failed. Please try again.
                </p>
              )}

            </div>
          </div>
        )}
      </div>
    </div>
  );
}