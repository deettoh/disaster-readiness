export default function LegendPanel() {

  return (
    <div className="absolute bottom-6 left-6 bg-gray/95 backdrop-blur-md
      border rounded-xl shadow-lg p-4 text-xs space-y-1 z-40 w-40">

      <h3 className="font-semibold text-sm border-b pb-1">
        Map Legend
      </h3>

      {/* Readiness */}
      <div className="space-y-1">
        <p className="font-medium">Readiness Level</p>

        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded"
            style={{ background: "#166534" }} />
          <span>High Readiness</span>
        </div>

        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded"
            style={{ background: "#facc15" }} />
          <span>Medium Readiness</span>
        </div>

        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded"
            style={{ background: "#ef4444" }} />
          <span>Low Readiness</span>
        </div>
      </div>

      {/* Hazard */}
      <div className="space-y-1">
        <p className="font-medium">Hazard Reports</p>

        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-blue-600" />
          <span>Flood</span>
        </div>

        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-red-600" />
          <span>Fire</span>
        </div>

        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-yellow-500" />
          <span>Landslide</span>
        </div>

        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-green-600" />
          <span>Normal</span>
        </div>
      </div>

      {/* Shelter */}
      <div className="flex items-center gap-2">
        <span className="w-3 h-3 rounded-full border-2 border-white
          bg-blue-500" />
        <span>Shelter</span>
      </div>

      {/* Route */}
      <div className="flex items-center gap-1">
        <span className="w-4 h-1 bg-[#5773a0]" />
        <span>Route Path</span>
      </div>

    </div>
  );
}