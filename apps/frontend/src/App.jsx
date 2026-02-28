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
                <p><strong>Type:</strong> {selectedHazard.label}</p>
                <p><strong>Confidence:</strong> {selectedHazard.confidence}</p>
                <p><strong>Observed:</strong> {selectedHazard.observed_at}</p>
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

    </div>
  );
}