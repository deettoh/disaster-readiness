import { useEffect, useState , useRef} from "react";
import MapView from "./components/MapView"; 
import ReportModal from "./components/report/ReportModal"; 
import HazardPanel from "./components/panels/HazardPanel";
import ReadinessPanel from "./components/panels/ReadinessPanel";
import AlertsPanel from "./components/panels/AlertsPanel";
import RoutePanel from "./components/panels/RoutePanel";
import { getMockAlerts } from "./mock/mockAlerts"; // remove when real API is ready
import { shelterCSVToGeoJSON } from "./utils/geojson";
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
    setSelectedAlertId(alert.alert_id);
    setActivePanel("alerts");
    setZoomTrigger({
      cell: alert.cell_id,
      time: Date.now()
    });
  };
  const [selectedAlertId, setSelectedAlertId] = useState(null);
  const [origin, setOrigin] = useState(null);
  const [shelters, setShelters] = useState([]);
  const [routeGeoJSON, setRouteGeoJSON] = useState(null);
  const [routeSummary, setRouteSummary] = useState(null);
  const [selectedShelter, setSelectedShelter] = useState("");
  const [mobilePanelOpen, setMobilePanelOpen] = useState(false);
  const [mobilePanelExpanded, setMobilePanelExpanded] = useState(false);
  const [panelHeight, setPanelHeight] = useState(45);

  const panelHeightRef = useRef(panelHeight);
  const dragStartYRef = useRef(null);
  const lastMoveTimeRef = useRef(0);
  const velocityRef = useRef(0);
  const animationFrameRef = useRef(null);

  const handleDragStart = (e) => {
    dragStartYRef.current = e.touches[0].clientY;
    lastMoveTimeRef.current = performance.now();

    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
  };

  const handleDragMove = (e) => {
    if (dragStartYRef.current === null) return;

    const now = performance.now();

    const currentY = e.touches[0].clientY;

    const deltaY = dragStartYRef.current - currentY;

    const dt = Math.max(1, now - lastMoveTimeRef.current);

    velocityRef.current = deltaY / dt;

    const screenHeight = window.innerHeight;
    const deltaPercent = (deltaY / screenHeight)*5;

    let newHeight = panelHeightRef.current + deltaPercent;

    newHeight = Math.max(25, Math.min(90, newHeight));

    panelHeightRef.current = newHeight;
    setPanelHeight(newHeight);

    lastMoveTimeRef.current = now;
  };

  const handleDragEnd = () => {
    dragStartYRef.current = null;

    const velocity = velocityRef.current;

    let targetHeight;

    // Flick physics snapping
    if (velocity > 1.5) {
      targetHeight = 90; // flick up → expand
    } else if (velocity < -1.5) {
      targetHeight = 50; // flick down → collapse
    } else {
      // Normal snap behaviour
      if (panelHeightRef.current > 70) targetHeight = 90;
      else if (panelHeightRef.current > 45) targetHeight = 55;
      else targetHeight = 30;
    }

    animatePanelSnap(targetHeight);
  };

  const animatePanelSnap = (target) => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }

    const start = panelHeightRef.current;
    const duration = 200;
    const startTime = performance.now();

    const animate = (time) => {
      const progress = Math.min((time - startTime) / duration, 1);

      const ease = 1 - Math.pow(1 - progress, 3);

      const value = start + (target - start) * ease;

      panelHeightRef.current = value;
      setPanelHeight(value);

      if (progress < 1) {
        animationFrameRef.current = requestAnimationFrame(animate);
      }
    };

    animationFrameRef.current = requestAnimationFrame(animate);
  };

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

  useEffect(() => {
    async function loadShelters() {
      const geojson = await shelterCSVToGeoJSON("../public/pj_shelters.csv");
      setShelters(geojson.features);
    }

    loadShelters();
  }, []);

  useEffect(() => {
    if (activePanel !== "route") {
      setOrigin(null);
      setRouteGeoJSON(null);
    }
  }, [activePanel]);

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
            onCellHover={(cell) => setHoveredCell(cell)}
            setReadinessGeoJSON={setReadinessGeoJSON}
            zoomCell={zoomTrigger}

            shelters={shelters}
            selectedShelter={selectedShelter}
            origin={origin}
            setOrigin={setOrigin}
            routeGeoJSON={routeGeoJSON}
            activePanel={activePanel}
          />
          
          {/* Floating Report Button */}
          <button
            onClick={() => setReportOpen(true)}
            className="absolute bottom-9 right-2 bg-red-600 text-white px-4 py-3 rounded-full shadow-lg hover:bg-red-700 transition z-40"
          >
            Report Hazard
          </button>
         {/* Mobile Panel Tabs */}
         <div className="md:hidden absolute bottom-0 left-0 right-0 bg-white border-t flex z-40">
            {["hazards","readiness","alerts","route"].map(tab => (
              <button
                key={tab}
                onClick={() => {
                  setActivePanel(tab);
                  setMobilePanelOpen(true);
                  setMobilePanelExpanded(false);
                }}
                className="flex-1 p-3 text-xs capitalize text-gray-600"
              >
                {tab}
              </button>
            ))}

          </div>
          {/* Mobile Bottom Sheet */}
          {mobilePanelOpen && (
            <div
              className="md:hidden absolute left-0 right-0 bg-white shadow-xl z-50 transition-all"
              style={{
                height: `${panelHeight}vh`,
                bottom: 0,
                transition: dragStartYRef.current ? "none" : "height 0.18s cubic-bezier(.4,0,.2,1)"
              }}
            >

              {/* Drag Handle */}
              <div
                style={{
                  width: "60px",
                  height: "12px",
                  background: "#d1d5db",
                  borderRadius: "999px",
                  margin: "10px auto",
                  touchAction: "none"
                }}
                onTouchStart={handleDragStart}
                onTouchMove={handleDragMove}
                onTouchEnd={handleDragEnd}
              />

              {/* Tabs */}
              <div className="flex border-b text-xs">

                {["hazards","readiness","alerts","route"].map(tab => (
                  <button
                    key={tab}
                    onClick={() => setActivePanel(tab)}
                    className={`flex-1 p-3 capitalize
                      ${activePanel === tab
                        ? "border-b-2 border-red-600 text-red-600 font-semibold"
                        : "text-gray-500"}
                    `}
                  >
                    {tab}
                  </button>
                ))}

                <button
                  onClick={() => setMobilePanelOpen(false)}
                  className="px-3 text-gray-400"
                >
                  ✕
                </button>

              </div>

              {/* Panel Content */}
              <div className="p-4 overflow-y-auto h-full">

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

                {activePanel === "route" && (
                  <RoutePanel
                    origin={origin}
                    shelters={shelters}
                    selectedShelter={selectedShelter}
                    setSelectedShelter={setSelectedShelter}
                    setOrigin={setOrigin}
                    onDrawRoute={(geojson) => setRouteGeoJSON(geojson)}
                    onClearRoute={() => {
                      setRouteGeoJSON(null);
                      setOrigin(null);
                      setSelectedShelter("");
                    }}
                  />
                )}

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

            {activePanel === "route" && (
              <RoutePanel
                origin={origin}
                shelters={shelters}
                selectedShelter={selectedShelter}
                setSelectedShelter={setSelectedShelter}
                setOrigin={setOrigin}
                onDrawRoute={(geojson) => {
                  setRouteGeoJSON(geojson);
                }}

                onClearRoute={() => {
                  setRouteGeoJSON(null);
                  setRouteSummary?.(null);
                  setOrigin(null);
                  setSelectedShelter("");
                }}
              />
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
