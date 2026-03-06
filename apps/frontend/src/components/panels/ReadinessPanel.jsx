import { useMemo } from "react";

/**
 * ReadinessPanel component shows detailed information about the hovered cell's readiness score and breakdown, as well as an overall summary of readiness across all cells. It updates dynamically based on the hovered cell and the readiness GeoJSON data.
 * @param {*} param0 
 * @returns 
 */
export default function ReadinessPanel({
  hoveredCell,
  readinessGeoJSON,
}) {
  const cell = hoveredCell?.properties;

  // Parse breakdown safely
  const breakdown =
    cell?.breakdown
      ? typeof cell.breakdown === "string"
        ? JSON.parse(cell.breakdown)
        : cell.breakdown
      : null;

  // Summary calculation
  const summary = useMemo(() => {
    if (!readinessGeoJSON?.features) return null;

    let totalScore = 0;
    let high = 0;
    let medium = 0;
    let low = 0;

    const n = readinessGeoJSON.features.length;

    readinessGeoJSON.features.forEach((f) => {
      const score = f.properties.score ?? 0;
      totalScore += score;

      if (score >= 70) high++;
      else if (score >= 40) medium++;
      else low++;
    });

    return {
      average: n ? (totalScore / n).toFixed(1) : "0.0",
      high,
      medium,
      low,
      totalCells: n,
    };
  }, [readinessGeoJSON]);

  return (
    <div className="space-y-6 text-sm text-gray-700">

      {/* Cell Readiness */}
      <div>
        <h2 className="text-base font-semibold mb-3">
          Cell Readiness
        </h2>

        {cell ? (
          <div className="space-y-3">

            <p>
              <strong>Name:</strong>{" "}
              {cell.name || cell.NEIGHBOURHOOD || "Unknown"}
            </p>

            <p>
              <strong>Score:</strong>{" "}
              <span className="font-semibold">
                {cell.score?.toFixed(1)}%
              </span>
            </p>

            {/* Breakdown */}
            {breakdown && (
              <div className="space-y-3 pt-2">
                {Object.entries(breakdown).map(([key, value]) => (
                  <div key={key}>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="capitalize">
                        {key.replace(/_/g, " ")}
                      </span>
                      <span>{(value * 100).toFixed(0)}%</span>
                    </div>

                    <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-500 transition-all duration-300"
                        style={{ width: `${value * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}

            <p className="text-xs text-gray-400 pt-2">
              Updated:{" "}
              {cell.updated_at
                ? new Date(cell.updated_at).toLocaleString()
                : "N/A"}
            </p>

          </div>
        ) : (
          <p className="text-gray-500">
            Hover over a neighbourhood cell to view readiness details.
          </p>
        )}
      </div>

      {/* PJ Summary */}
      {summary && (
        <div>
          <h2 className="text-base font-semibold mb-3">
            PJ Overall Readiness
          </h2>

          <div className="space-y-2">

            <p>
              <strong>Average Score:</strong>{" "}
              {summary.average}%
            </p>

            <p>
              <strong>Total Cells:</strong>{" "}
              {summary.totalCells}
            </p>

            <div className="grid grid-cols-3 gap-3 pt-3 text-center">

              <div className="p-3 rounded-lg bg-green-100 text-green-700">
                <div className="font-semibold">
                  {summary.high}
                </div>
                <div className="text-xs">
                  High (≥70%)
                </div>
              </div>

              <div className="p-3 rounded-lg bg-yellow-100 text-yellow-700">
                <div className="font-semibold">
                  {summary.medium}
                </div>
                <div className="text-xs">
                  Medium (40–69%)
                </div>
              </div>

              <div className="p-3 rounded-lg bg-red-100 text-red-700">
                <div className="font-semibold">
                  {summary.low}
                </div>
                <div className="text-xs">
                  Low (&lt;40%)
                </div>
              </div>

            </div>
          </div>
        </div>
      )}

    </div>
  );
}