import { useEffect, useState } from "react";
import MapView from "./components/MapView"; 
import ReportModal from "./components/report/ReportModal"; 
import HazardPanel from "./components/panels/HazardPanel";
import ReadinessPanel from "./components/panels/ReadinessPanel";
import AlertsPanel from "./components/panels/AlertsPanel";
import RoutePanel from "./components/panels/RoutePanel";
import { getMockAlerts } from "./mock/mockAlerts"; // remove when real API is ready
/** 
 * Main entry point of the application. 
 * Overall layout: nav bar, full-screen map, and desktop side panel. 
 */
export default function App() {
  const [selectedHazard, setSelectedHazard] = useState(null);
  const [reportOpen, setReportOpen] = useState(false);
  const [imagePopup, setImagePopup] = useState(null);
  const [showMobileInfo, setShowMobileInfo] = useState(true);
  const [activePanel, setActivePanel] = useState("hazards");
  const [hoveredCell, setHoveredCell] = useState(null);
  const [readinessGeoJSON, setReadinessGeoJSON] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [popupAlert, setPopupAlert] = useState(null);
  const [zoomTrigger, setZoomTrigger] = useState({
    cell: null,
    time: 0
  });
  const handleAlertClick = (alert) => {
    if (!alert?.cell_id) return;
    setSelectedAlertId(popupAlert.alert_id);
    setActivePanel("alerts");
    setZoomTrigger({
      cell: alert.cell_id,
      time: Date.now()
    });
  };
  const [selectedAlertId, setSelectedAlertId] = useState(null);

 useEffect(() => {
    let interval;

    async function pollAlerts() {
      try {
        const data = await getMockAlerts();
        // fetch api here when ready, using mock for now
        // const response = await fetch(`${API_BASE_URL}/alerts`);
        // const data = await response.json();
        if (!data?.items) return;

        setAlerts(prev => {
          const existingIds = new Set(prev.map(a => a.alert_id));

          const newItems = data.items.filter(
            a => !existingIds.has(a.alert_id)
          );

          if (newItems.length > 0) {
            setPopupAlert(newItems[0]);
          }

          return [...newItems, ...prev];
        });

      } catch (err) {
        console.error("Alert polling failed", err);
      }
    }

    pollAlerts();
    interval = setInterval(pollAlerts, 10000);

    return () => clearInterval(interval);
  }, []);

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
            onCellHover={(cell) => {
              setHoveredCell(cell);
            }}
            setReadinessGeoJSON={setReadinessGeoJSON}
            zoomCell={zoomTrigger}
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

          {/* Tabs */}
          <div className="flex border-b text-sm">
            {["hazards", "readiness", "alerts", "route"].map((tab) => (
              <button
                key={tab}
                onClick={() => setActivePanel(tab)}
                className={`flex-1 p-3 capitalize transition
                  ${activePanel === tab
                    ? "border-b-2 border-red-600 font-semibold text-red-600"
                    : "text-gray-500 hover:bg-gray-100"
                  }`}
              >
                {tab}
              </button>
            ))}
          </div>

          {/* Panel Content */}
          <div className="p-4 overflow-y-auto flex-1">
            {activePanel === "hazards" && (
              <HazardPanel
                selectedHazard={selectedHazard}
                setImagePopup={setImagePopup}
              />
            )}

            {activePanel === "readiness" && (
              <ReadinessPanel
                hoveredCell={hoveredCell}
                readinessGeoJSON={readinessGeoJSON}
              />
            )}

            {activePanel === "alerts" && (
              <AlertsPanel
                alerts={alerts}
                onAlertClick={handleAlertClick}
                selectedAlertId={selectedAlertId}
              />
            )}

            {activePanel === "route" && <RoutePanel />}
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
      {popupAlert && (
        <div
          className="fixed bottom-6 right-6 z-50 w-80 animate-slide-up cursor-pointer"
          onClick={() => {
            setSelectedAlertId(popupAlert.alert_id);
            setActivePanel("alerts");
            setZoomTrigger({
              cell: popupAlert.cell_id,
              time: Date.now()
            });
          }}
        >
          <div className="bg-red-100 border border-red-200 rounded-xl shadow-xl p-4 space-y-2">

            {/* Header */}
            <div className="flex justify-between items-center">

              <div className="flex items-center gap-2">

                <span className="font-bold text-sm text-red-700">
                  ALERT
                </span>

                <span className={`
                  text-xs px-2 py-0.5 rounded-full capitalize
                  ${popupAlert.level === "high"
                    ? "bg-red-200 text-red-800"
                    : popupAlert.level === "medium"
                    ? "bg-yellow-100 text-yellow-700"
                    : "bg-green-100 text-green-700"}
                `}>
                  {popupAlert.level}
                </span>

              </div>

              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setPopupAlert(null);
                }}
                className="text-red-500 hover:text-red-700 transition"
              >
                ✕
              </button>

            </div>

            {/* Message */}
            <p className="text-sm text-red-900 leading-snug">
              {popupAlert.message}
            </p>

          </div>
        </div>
      )}

    </div>
  );
}