import { useEffect, useState } from "react";

/**
 *  AlertsPanel component displays a list of active alerts with sorting and click-to-zoom functionality.
 * @param {*} param0 
 * @returns 
 */
export default function AlertsPanel({ alerts, onAlertClick, selectedAlertId }) {
  const [sortMode, setSortMode] = useState("latest");

  const sortedAlerts = [...alerts].sort((a, b) => {
    if (sortMode === "latest") {
      return new Date(b.created_at) - new Date(a.created_at);
    }

    const severityRank = { high: 3, medium: 2, low: 1 };
    return severityRank[b.level] - severityRank[a.level];
  });

  const levelColor = (level) => {
    switch (level) {
      case "high":
        return "bg-red-100 text-red-700";
      case "medium":
        return "bg-yellow-100 text-yellow-700";
      case "low":
        return "bg-green-100 text-green-700";
      default:
        return "bg-gray-100 text-gray-700";
    }
  };

  return (
    <div className="space-y-4 text-sm">

      <div className="flex justify-between items-center">
        <h2 className="font-semibold text-base">Alerts</h2>

        <select
          className="border rounded p-1 text-xs"
          value={sortMode}
          onChange={(e) => setSortMode(e.target.value)}
        >
          <option value="latest">Latest</option>
          <option value="severity">Severity</option>
        </select>
      </div>

      {sortedAlerts.length === 0 && (
        <p className="text-gray-500">No alerts</p>
      )}

      {sortedAlerts.map(alert => (
        <div
          key={alert.alert_id}
          onClick={() => onAlertClick(alert)}
          className={`border rounded-lg p-3 cursor-pointer transition
                      hover:bg-gray-50
                      ${alert.alert_id === selectedAlertId
                        ? "border-red-500 bg-red-50 shadow-md scale-[1.02]"
                        : ""
                      }
                    `}
        >
          <div className="flex justify-between mb-1">

            <span className={`text-xs px-2 py-1 rounded ${levelColor(alert.level)}`}>
              {alert.level.toUpperCase()}
            </span>

            <span className="text-xs text-gray-400">
              {new Date(alert.created_at).toLocaleTimeString()}
            </span>

          </div>

          <p className="font-medium text-sm">
            {alert.message}
          </p>

          <p className="text-xs text-gray-500">
            Cell: {alert.cell_id}
          </p>

        </div>
      ))}

    </div>
  );
}