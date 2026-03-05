/**
 *  HazardPanel component shows detailed information about a selected hazard, including report ID, type, confidence level, observed time, and an image if available. It also provides a tooltip warning for low confidence hazards and allows users to click the image for a larger view.
 * @param {*} param0 
 * @returns 
 */
export default function HazardPanel({
  selectedHazard,
  setImagePopup,
}) {
  return (
    <div className="text-sm text-gray-600">
      {selectedHazard ? (
        <div className="space-y-2">

          {/* Report ID */}
          <p>
            <strong>Report ID:</strong>{" "}
            {selectedHazard.report_id || "N/A"}
          </p>

          {/* Type */}
          <p>
            <strong>Type:</strong>{" "}
            {selectedHazard.label || "N/A"}
          </p>

          {/* Confidence */}
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
                                 bg-amber-100 text-amber-700 
                                 border border-amber-300 
                                 font-semibold 
                                 hover:bg-amber-200 
                                 transition"
                    >
                      Uncertain
                    </button>

                    {/* Tooltip */}
                    <div
                      id="confidence-tooltip"
                      role="tooltip"
                      className="absolute left-1/2 -translate-x-1/2 
                                 bottom-full mb-3 w-64
                                 opacity-0 translate-y-1
                                 group-hover:opacity-100 
                                 group-hover:translate-y-0
                                 transition-all duration-200 ease-out
                                 pointer-events-none
                                 bg-slate-800 text-slate-100 
                                 text-xs rounded-xl 
                                 px-3 py-2
                                 shadow-xl 
                                 border border-slate-600 
                                 z-50"
                    >
                      Warning: Low confidence level detected. Please manually verify this hazard before taking any action.

                      {/* Arrow */}
                      <div
                        className="absolute left-1/2 -translate-x-1/2 top-full
                                   w-0 h-0
                                   border-l-8 border-r-8 border-t-8
                                   border-l-transparent 
                                   border-r-transparent 
                                   border-t-slate-800"
                      />
                    </div>
                  </div>
                )}
              </>
            ) : (
              "N/A"
            )}
          </p>

          {/* Observed */}
          <p>
            <strong>Observed:</strong>{" "}
            {selectedHazard.observed_at
              ? new Date(
                  selectedHazard.observed_at
                ).toLocaleString()
              : "N/A"}
          </p>

          {/* Image */}
          {selectedHazard.redacted_image_url && (
            <div className="space-y-1 pt-2">
              <p className="font-medium">Image</p>

              <img
                src={selectedHazard.redacted_image_url}
                alt="Hazard"
                className="w-56 rounded-xl shadow cursor-pointer hover:opacity-90 transition"
                onClick={() =>
                  setImagePopup(
                    selectedHazard.redacted_image_url
                  )
                }
              />
            </div>
          )}

        </div>
      ) : (
        <p>Click a hazard to see details.</p>
      )}
    </div>
  );
}