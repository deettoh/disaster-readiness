import { useState } from "react"; 
import MapView from "./components/MapView"; 
import ReportModal from "./components/report/ReportModal"; 
/** 
 * Main entry point of the application. 
 * Overall layout: nav bar, full-screen map, and desktop side panel. 
 */
export default function App() {
  const [selectedHazard, setSelectedHazard] = useState(null);
  const [reportOpen, setReportOpen] = useState(false);
  const [imagePopup, setImagePopup] = useState(null);
  const [showMobileInfo, setShowMobileInfo] = useState(true);

  return (
    <div className="h-screen w-screen flex flex-col">
      
      {/* Top Navigation */}
      <header className="h-14 bg-gray-900 text-white flex items-center px-4">
        <h1 className="font-semibold text-sm md:text-base">
          Malaysia Disaster Readiness
        </h1>
      </header>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        
        {/* Map */}
        <div className="flex-1 relative">
          <MapView
            onHazardClick={(hazard) => {
              setSelectedHazard(hazard);
              setShowMobileInfo(true);
            }}
          />
          
          {/* Floating Report Button */}
          <button
            onClick={() => setReportOpen(true)}
            className="absolute bottom-9 right-2 bg-red-600 text-white px-4 py-3 rounded-full shadow-lg hover:bg-red-700 transition z-40"
          >
            Report Hazard
          </button>
          {/* Mobile Bottom Info Panel */}
          {selectedHazard && showMobileInfo && (
          <div className="md:hidden absolute bottom-0 left-0 right-0 bg-white rounded-t-2xl shadow-lg p-4 z-40 animate-slide-up">
            
            {/* Drag Indicator */}
            <div className="w-12 h-1 bg-gray-300 rounded-full mx-auto mb-3"></div>

            {/* Close Button */}
            <div className="flex justify-between items-start">
              <h3 className="font-semibold text-sm">Hazard Details</h3>
              <button
                onClick={() => setShowMobileInfo(false)}
                className="text-gray-400 text-sm"
              >
                ✕
              </button>
            </div>

            <div className="space-y-2 text-sm mt-2">
              <p><strong>Type:</strong> {selectedHazard.label}</p>
              <p><strong>Confidence:</strong> {selectedHazard.confidence}</p>
              <p><strong>Observed:</strong> {selectedHazard.observed_at}</p>
            </div>

          </div>
        )}
        </div>

        {/* Desktop Side Panel */}
        <div className="hidden md:flex w-96 bg-white border-l flex-col">
          <div className="p-4 font-semibold border-b">
            Info Panel
          </div>

          <div className="p-4 text-sm text-gray-600">
            {selectedHazard ? (
              <div className="space-y-2">

                <p>
                  <strong>Report ID:</strong>{" "}
                  {selectedHazard.report_id || "N/A"}
                </p>

                <p>
                  <strong>Type:</strong>{" "}
                  {selectedHazard.label || "N/A"}
                </p>

                <p className="flex items-center gap-2">
                  <strong>Confidence:</strong>

                  {selectedHazard.confidence !== undefined ? (
                    <>
                      <span>
                        {(Number(selectedHazard.confidence) * 100).toFixed(0)}%
                      </span>

                      {Number(selectedHazard.confidence) < 0.5 && (
                        <div className="relative inline-flex group">
                          <button
                            type="button"
                            aria-describedby="confidence-tooltip"
                            className="px-2.5 py-1 text-xs rounded-full 
                                      bg-amber-100 text-amber-700 border border-amber-300 
                                      font-semibold hover:bg-amber-200 transition"
                          >
                            Uncertain
                          </button>

                          {/* Tooltip */}
                          <div
                            id="confidence-tooltip"
                            role="tooltip"
                            className="absolute left-1/2 -translate-x-1/2 bottom-full mb-3 w-64
                                      opacity-0 translate-y-1
                                      group-hover:opacity-100 group-hover:translate-y-0
                                      transition-all duration-200 ease-out
                                      pointer-events-none
                                      bg-slate-800 text-slate-100 text-xs rounded-xl px-3 py-2
                                      shadow-xl border border-slate-600 z-50"
                          >
                            Warning: Low confidence level detected. Please manually verify this hazard
                            before taking any action.

                            {/* Arrow */}
                            <div className="absolute left-1/2 -translate-x-1/2 top-full
                                            w-0 h-0
                                            border-l-8 border-r-8 border-t-8
                                            border-l-transparent border-r-transparent border-t-slate-800" />
                          </div>
                        </div>
                      )}
                    </>
                  ) : (
                    "N/A"
                  )}
                </p>

                <p>
                  <strong>Observed:</strong>{" "}
                  {selectedHazard.observed_at
                    ? new Date(selectedHazard.observed_at).toLocaleString()
                    : "N/A"}
                </p>

                {selectedHazard.redacted_image_url && (
                  <div className="space-y-1 pt-2">
                    <p className="font-medium">Image</p>

                    <img
                      src={selectedHazard.redacted_image_url}
                      className="w-56 rounded-xl shadow cursor-pointer hover:opacity-90 transition"
                      onClick={() => setImagePopup(selectedHazard.redacted_image_url)}
                    />
                  </div>
                )}

              </div>
            ) : (
              <p>Click a hazard to see details.</p>
            )}
          </div>
        </div>

      </div>

      <ReportModal
        open={reportOpen}
        onClose={() => setReportOpen(false)}
      />
      {imagePopup && (
        <div
          className="fixed inset-0 bg-black/70 flex items-center justify-center z-50"
          onClick={() => setImagePopup(null)}
        >
          <img
            src={imagePopup}
            className="max-w-[90vw] max-h-[90vh] rounded-xl"
          />
        </div>
      )}

    </div>
  );
}