export default function LegendPanel({ layers, toggleLayer }) {

  return (
    <div className="absolute bottom-12 md:bottom-6 left-2 md:left-6 bg-gray/95 backdrop-blur-md
      border rounded-xl shadow-lg p-2 md:p-4 text-[10px] md:text-xs space-y-1.5 md:space-y-2 z-40 w-32 md:w-44">

      <h3 className="font-semibold text-[14px] md:text-sm border-b pb-1">
        Map Legend
      </h3>

      {/* Readiness */}
      <div className="space-y-1">
        <p className="font-medium">Readiness Level</p>

        <div
          onClick={() => toggleLayer("highReadiness")}
          className={`flex items-center gap-2 cursor-pointer transition-opacity duration-150
          ${layers.highReadiness ? "opacity-100" : "opacity-30"}`}
        >
          <span className="w-3 h-3 rounded"
            style={{ background: "#166534" }} />
          <span>High Readiness</span>
        </div>

        <div
          onClick={() => toggleLayer("mediumReadiness")}
          className={`flex items-center gap-2 cursor-pointer transition-opacity duration-150
          ${layers.mediumReadiness ? "opacity-100" : "opacity-30"}`}
        >
          <span className="w-3 h-3 rounded"
            style={{ background: "#facc15" }} />
          <span>Medium Readiness</span>
        </div>

        <div
          onClick={() => toggleLayer("lowReadiness")}
          className={`flex items-center gap-2 cursor-pointer transition-opacity duration-150
          ${layers.lowReadiness ? "opacity-100" : "opacity-30"}`}
        >
          <span className="w-3 h-3 rounded"
            style={{ background: "#ef4444" }} />
          <span>Low Readiness</span>
        </div>

      </div>

      {/* Hazards */}
      <div className="space-y-1">
        <p className="font-medium">Hazard Reports</p>

        <div
          onClick={() => toggleLayer("flood")}
          className={`flex items-center gap-2 cursor-pointer transition-opacity duration-150
          ${layers.flood ? "opacity-100" : "opacity-30"}`}
        >
          <span className="w-3 h-3 rounded-full bg-blue-600"/>
          <span>Flood</span>
        </div>

        <div
          onClick={() => toggleLayer("fire")}
          className={`flex items-center gap-2 cursor-pointer transition-opacity duration-150
          ${layers.fire ? "opacity-100" : "opacity-30"}`}
        >
          <span className="w-3 h-3 rounded-full bg-red-600"/>
          <span>Fire</span>
        </div>

        <div
          onClick={() => toggleLayer("landslide")}
          className={`flex items-center gap-2 cursor-pointer transition-opacity duration-150
          ${layers.landslide ? "opacity-100" : "opacity-30"}`}
        >
          <span className="w-3 h-3 rounded-full bg-yellow-500"/>
          <span>Landslide</span>
        </div>

        <div
          onClick={() => toggleLayer("normal")}
          className={`flex items-center gap-2 cursor-pointer transition-opacity duration-150
          ${layers.normal ? "opacity-100" : "opacity-30"}`}
        >
          <span className="w-3 h-3 rounded-full bg-green-600"/>
          <span>Normal</span>
        </div>

      </div>

      {/* Shelter */}
      <div
        onClick={() => toggleLayer("shelter")}
        className={`flex items-center gap-2 cursor-pointer transition-opacity duration-150
        ${layers.shelter ? "opacity-100" : "opacity-30"}`}
      >
        <span className="w-3 h-3 rounded-full border-2 border-white bg-blue-500"/>
        <span>Shelter</span>
      </div>

      {/* Route */}
      <div
        onClick={() => toggleLayer("route")}
        className={`flex items-center gap-1 cursor-pointer transition-opacity duration-150
        ${layers.route ? "opacity-100" : "opacity-30"}`}
      >
        <span className="w-4 h-1 bg-[#5773a0]" />
        <span>Route Path</span>
      </div>

    </div>
  );
}