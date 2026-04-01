import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell,
} from "recharts";
import { useRun } from "../api/hooks";
import StatusBadge from "../components/StatusBadge";
import ScoreBar from "../components/ScoreBar";
import type { EntryResult } from "../api/types";

export default function RunDetail() {
  const { id } = useParams<{ id: string }>();
  const { data: run, isLoading } = useRun(id!);
  const [expandedEntry, setExpandedEntry] = useState<number | null>(null);

  if (isLoading) return <p className="text-gray-500">Loading run...</p>;
  if (!run) return <p className="text-gray-500">Run not found.</p>;

  const radarData =
    run.dimension_breakdown?.map((d) => ({
      dimension: d.dimension,
      score: d.mean_score,
      fullMark: 5,
    })) ?? [];

  const entryBarData =
    run.entry_results?.map((e) => ({
      name: `#${e.entry_index}`,
      score: e.aggregated_score,
    })) ?? [];

  const heatmapDimensions = [
    ...new Set(
      run.entry_results?.flatMap((e) =>
        e.judge_scores.map((j) => j.dimension)
      ) ?? []
    ),
  ];

  return (
    <div>
      <Link
        to="/runs"
        className="text-sm text-gray-500 hover:text-gray-300 mb-4 inline-block"
      >
        &larr; Back to runs
      </Link>

      <div className="flex items-center gap-4 mb-6">
        <h1 className="text-2xl font-bold text-white">
          Run {run.id.slice(0, 8)}...
        </h1>
        <StatusBadge status={run.status} />
      </div>

      {run.status === "running" && (
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4 mb-6">
          <p className="text-amber-400 text-sm">
            Evaluation in progress... auto-refreshing every 3s.
          </p>
        </div>
      )}

      {run.status === "failed" && run.error_message && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 mb-6">
          <p className="text-red-400 text-sm">{run.error_message}</p>
        </div>
      )}

      {run.status === "completed" && (
        <>
          {/* Score + Stats cards */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-8">
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 md:col-span-1">
              <p className="text-xs text-gray-500 uppercase tracking-wider">
                Overall
              </p>
              <p className="text-3xl font-bold text-white mt-1">
                {run.overall_score?.toFixed(2)}
              </p>
            </div>
            {run.stats && (
              <>
                <MiniStat label="Mean" value={run.stats.mean} />
                <MiniStat label="Median" value={run.stats.median} />
                <MiniStat label="Std Dev" value={run.stats.std} />
                <MiniStat
                  label="Range"
                  value={`${run.stats.min.toFixed(1)}-${run.stats.max.toFixed(1)}`}
                />
              </>
            )}
          </div>

          {/* Charts row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            {radarData.length > 0 && (
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
                <h2 className="text-sm font-medium text-gray-300 mb-4">
                  Dimension Radar
                </h2>
                <ResponsiveContainer width="100%" height={280}>
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
                    <Radar
                      dataKey="score"
                      stroke="#818cf8"
                      fill="#818cf8"
                      fillOpacity={0.3}
                    />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            )}

            {entryBarData.length > 0 && (
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
                <h2 className="text-sm font-medium text-gray-300 mb-4">
                  Score per Entry
                </h2>
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={entryBarData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                    <XAxis
                      dataKey="name"
                      tick={{ fill: "#9ca3af", fontSize: 11 }}
                    />
                    <YAxis
                      domain={[0, 5]}
                      tick={{ fill: "#6b7280", fontSize: 11 }}
                    />
                    <Tooltip
                      contentStyle={{
                        background: "#111827",
                        border: "1px solid #374151",
                        borderRadius: "8px",
                        color: "#e5e7eb",
                      }}
                    />
                    <Bar dataKey="score" radius={[4, 4, 0, 0]}>
                      {entryBarData.map((d, i) => (
                        <Cell
                          key={i}
                          fill={
                            d.score >= 3
                              ? "#34d399"
                              : d.score >= 2
                                ? "#fbbf24"
                                : "#f87171"
                          }
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          {/* Heatmap */}
          {run.entry_results && run.entry_results.length > 0 && (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 mb-8">
              <h2 className="text-sm font-medium text-gray-300 mb-4">
                Score Heatmap (Entries x Dimensions)
              </h2>
              <div className="overflow-x-auto">
                <table className="text-xs">
                  <thead>
                    <tr>
                      <th className="px-3 py-2 text-gray-500 text-left">
                        Entry
                      </th>
                      {heatmapDimensions.map((dim) => (
                        <th
                          key={dim}
                          className="px-3 py-2 text-gray-500 text-center capitalize"
                        >
                          {dim}
                        </th>
                      ))}
                      <th className="px-3 py-2 text-gray-500 text-center">
                        Agg
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {run.entry_results.map((entry) => (
                      <tr key={entry.entry_index}>
                        <td className="px-3 py-1.5 text-gray-400">
                          #{entry.entry_index}
                        </td>
                        {heatmapDimensions.map((dim) => {
                          const js = entry.judge_scores.find(
                            (s) => s.dimension === dim
                          );
                          const score = js?.score ?? 0;
                          return (
                            <td key={dim} className="px-3 py-1.5 text-center">
                              <span
                                className="inline-flex w-8 h-8 rounded items-center justify-center text-white font-medium text-xs"
                                style={{ background: heatColor(score) }}
                              >
                                {score}
                              </span>
                            </td>
                          );
                        })}
                        <td className="px-3 py-1.5 text-center">
                          <span
                            className="inline-flex w-10 h-8 rounded items-center justify-center text-white font-bold text-xs"
                            style={{
                              background: heatColor(entry.aggregated_score),
                            }}
                          >
                            {entry.aggregated_score.toFixed(1)}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Per-entry details */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
            <div className="px-5 py-3 border-b border-gray-800">
              <h2 className="text-sm font-medium text-gray-300">
                Entry Details
              </h2>
            </div>
            <div className="divide-y divide-gray-800/50">
              {run.entry_results?.map((entry) => (
                <EntryRow
                  key={entry.entry_index}
                  entry={entry}
                  expanded={expandedEntry === entry.entry_index}
                  onToggle={() =>
                    setExpandedEntry(
                      expandedEntry === entry.entry_index
                        ? null
                        : entry.entry_index
                    )
                  }
                />
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function MiniStat({
  label,
  value,
}: {
  label: string;
  value: number | string;
}) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <p className="text-xs text-gray-500 uppercase tracking-wider">{label}</p>
      <p className="text-xl font-bold text-white mt-1">
        {typeof value === "number" ? value.toFixed(2) : value}
      </p>
    </div>
  );
}

function EntryRow({
  entry,
  expanded,
  onToggle,
}: {
  entry: EntryResult;
  expanded: boolean;
  onToggle: () => void;
}) {
  return (
    <div>
      <button
        onClick={onToggle}
        className="w-full px-5 py-3 flex items-center gap-4 text-left hover:bg-gray-800/30 transition-colors"
      >
        <span className="text-xs text-gray-600 w-6">#{entry.entry_index}</span>
        <span className="flex-1 text-sm text-gray-300 truncate">
          {entry.input}
        </span>
        <div className="w-32">
          <ScoreBar score={entry.aggregated_score} />
        </div>
        <span className="text-gray-600 text-xs">{expanded ? "▲" : "▼"}</span>
      </button>
      {expanded && (
        <div className="px-5 pb-4 space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="bg-gray-950 rounded-lg p-3">
              <p className="text-xs text-gray-500 mb-1">Input</p>
              <p className="text-sm text-gray-300">{entry.input}</p>
            </div>
            <div className="bg-gray-950 rounded-lg p-3">
              <p className="text-xs text-gray-500 mb-1">Output</p>
              <p className="text-sm text-gray-300">{entry.output}</p>
            </div>
          </div>
          <div className="space-y-2">
            {entry.judge_scores.map((js) => (
              <div key={js.judge_name} className="bg-gray-950 rounded-lg p-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-medium text-gray-400 capitalize">
                    {js.dimension}
                  </span>
                  <span className="text-sm font-mono text-white">
                    {js.score}/5
                  </span>
                </div>
                <p className="text-xs text-gray-500">{js.reasoning}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function heatColor(score: number): string {
  if (score >= 4) return "#059669";
  if (score >= 3) return "#d97706";
  if (score >= 2) return "#dc2626";
  return "#7f1d1d";
}
