import MapView from "./components/MapView";

/**
 * Main entry point of the application.
 * Overall layout: nav bar, full-screen map, and desktop side panel.
 */
export default function App() {
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
          <MapView />
          
          {/* Floating Report Button */}
          <button className="absolute bottom-6 right-6 bg-red-600 text-white px-4 py-3 rounded-full shadow-lg hover:bg-red-700 transition">
            Report Hazard
          </button>
        </div>

        {/* Desktop Side Panel */}
        <div className="hidden md:flex w-96 bg-white border-l flex-col">
          <div className="p-4 font-semibold border-b">
            Info Panel
          </div>
          <div className="p-4 text-sm text-gray-600">
            Click a hazard or area to see details.
          </div>
        </div>

      </div>
    </div>
  );
}