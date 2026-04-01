import { useState, useMemo } from "react";
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { useRuns, useCompare } from "../api/hooks";

const COLORS = ["#818cf8", "#34d399", "#fbbf24", "#f87171"];

export default function Compare() {
  const { data: runs } = useRuns();
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const { data: comparison, isLoading } = useCompare(selectedIds);

  const completedRuns = runs?.filter((r) => r.status === "completed") ?? [];

  // Map run ID → readable label like "Customer Support Bot Eval"
  const runLabels = useMemo(() => {
    const map: Record<string, string> = {};
    if (!runs) return map;
    // Track how many times each suite_name appears to disambiguate
    const nameCount: Record<string, number> = {};
    for (const r of runs) {
      nameCount[r.suite_name] = (nameCount[r.suite_name] ?? 0) + 1;
    }
    const nameIndex: Record<string, number> = {};
    for (const r of runs) {
      if (nameCount[r.suite_name] > 1) {
        nameIndex[r.suite_name] = (nameIndex[r.suite_name] ?? 0) + 1;
        map[r.id] = `${r.suite_name} #${nameIndex[r.suite_name]}`;
      } else {
        map[r.id] = r.suite_name;
      }
    }
    return map;
  }, [runs]);

  const getLabel = (id: string) => runLabels[id] ?? id.slice(0, 8);

  const toggleRun = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const allDimensions = [
    ...new Set(
      comparison?.runs.flatMap(
        (r) => r.dimension_breakdown?.map((d) => d.dimension) ?? []
      ) ?? []
    ),
  ];

  const radarData = allDimensions.map((dim) => {
    const point: Record<string, string | number> = { dimension: dim };
    comparison?.runs.forEach((r) => {
      const db = r.dimension_breakdown?.find((d) => d.dimension === dim);
      point[getLabel(r.id)] = db?.mean_score ?? 0;
    });
    return point;
  });

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-1">Compare Runs</h1>
      <p className="text-gray-500 text-sm mb-8">
        Select 2+ completed runs to compare side-by-side
      </p>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 mb-8">
        <h2 className="text-sm font-medium text-gray-300 mb-3">
          Select Runs
        </h2>
        {completedRuns.length === 0 ? (
          <p className="text-gray-500 text-sm">
            No completed runs to compare.
          </p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {completedRuns.map((r) => (
              <button
                key={r.id}
                onClick={() => toggleRun(r.id)}
                className={`px-3 py-1.5 rounded-lg text-sm border transition-colors ${
                  selectedIds.includes(r.id)
                    ? "bg-indigo-600/20 border-indigo-500 text-indigo-400"
                    : "bg-gray-950 border-gray-700 text-gray-400 hover:border-gray-500"
                }`}
              >
                {r.suite_name} ({r.overall_score?.toFixed(2)})
              </button>
            ))}
          </div>
        )}
      </div>

      {selectedIds.length < 2 && (
        <p className="text-gray-600 text-sm">
          Select at least 2 runs to compare.
        </p>
      )}

      {isLoading && <p className="text-gray-500 text-sm">Loading...</p>}

      {comparison && comparison.runs.length >= 2 && (
        <>
          {/* Overall scores */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            {comparison.runs.map((r, i) => (
              <div
                key={r.id}
                className="bg-gray-900 border rounded-xl p-5"
                style={{ borderColor: COLORS[i % COLORS.length] + "66" }}
              >
                <p className="text-xs text-gray-500">{getLabel(r.id)}</p>
                <p
                  className="text-2xl font-bold mt-1"
                  style={{ color: COLORS[i % COLORS.length] }}
                >
                  {r.overall_score?.toFixed(2)}
                </p>
              </div>
            ))}
          </div>

          {/* Radar overlay */}
          {radarData.length > 0 && (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 mb-8">
              <h2 className="text-sm font-medium text-gray-300 mb-4">
                Dimension Comparison
              </h2>
              <ResponsiveContainer width="100%" height={350}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="#374151" />
                  <PolarAngleAxis
                    dataKey="dimension"
                    tick={{ fill: "#9ca3af", fontSize: 12 }}
                  />
                  <PolarRadiusAxis
                    angle={90}
                    domain={[0, 5]}
                    tick={{ fill: "#6b7280", fontSize: 10 }}
                  />
                  {comparison.runs.map((r, i) => (
                    <Radar
                      key={r.id}
                      name={getLabel(r.id)}
                      dataKey={getLabel(r.id)}
                      stroke={COLORS[i % COLORS.length]}
                      fill={COLORS[i % COLORS.length]}
                      fillOpacity={0.15}
                    />
                  ))}
                  <Legend />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Entry-level comparison table */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 overflow-x-auto">
            <h2 className="text-sm font-medium text-gray-300 mb-4">
              Per-Entry Score Deltas
            </h2>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-500 text-xs uppercase tracking-wider">
                  <th className="px-3 py-2 text-left">Entry</th>
                  {comparison.runs.map((r, i) => (
                    <th
                      key={r.id}
                      className="px-3 py-2 text-center"
                      style={{ color: COLORS[i % COLORS.length] }}
                    >
                      {getLabel(r.id)}
                    </th>
                  ))}
                  {comparison.runs.length === 2 && (
                    <th className="px-3 py-2 text-center">Delta</th>
                  )}
                </tr>
              </thead>
              <tbody>
                {(comparison.runs[0].entry_results ?? []).map((entry, idx) => {
                  const scores = comparison.runs.map(
                    (r) => r.entry_results?.[idx]?.aggregated_score ?? 0
                  );
                  const delta =
                    comparison.runs.length === 2
                      ? scores[1] - scores[0]
                      : null;
                  return (
                    <tr key={idx} className="border-t border-gray-800/50">
                      <td className="px-3 py-2 text-gray-300 max-w-[250px] truncate">
                        {entry.input.length > 50
                          ? entry.input.slice(0, 50) + "..."
                          : entry.input}
                      </td>
                      {scores.map((s, i) => (
                        <td
                          key={i}
                          className="px-3 py-2 text-center font-mono"
                        >
                          {s.toFixed(2)}
                        </td>
                      ))}
                      {delta !== null && (
                        <td
                          className={`px-3 py-2 text-center font-mono font-bold ${
                            delta > 0
                              ? "text-emerald-400"
                              : delta < 0
                                ? "text-red-400"
                                : "text-gray-500"
                          }`}
                        >
                          {delta > 0 ? "+" : ""}
                          {delta.toFixed(2)}
                        </td>
                      )}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
