import { useState } from "react";
import { Link } from "react-router-dom";
import { useRuns, useSuites, useDatasets, useStartRun } from "../api/hooks";
import StatusBadge from "../components/StatusBadge";

export default function Runs() {
  const { data: runs, isLoading } = useRuns();
  const { data: suites } = useSuites();
  const { data: datasets } = useDatasets();
  const startRun = useStartRun();
  const [suiteId, setSuiteId] = useState("");
  const [datasetId, setDatasetId] = useState("");

  const handleStart = () => {
    if (!suiteId || !datasetId) return;
    startRun.mutate(
      { suiteId, datasetId },
      {
        onSuccess: () => {
          setSuiteId("");
          setDatasetId("");
        },
      }
    );
  };

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-1">Evaluation Runs</h1>
      <p className="text-gray-500 text-sm mb-8">
        Trigger and monitor evaluation runs
      </p>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 mb-8">
        <h2 className="text-sm font-medium text-gray-300 mb-4">
          Start New Run
        </h2>
        <div className="flex flex-wrap items-end gap-4">
          <div className="flex-1 min-w-[180px]">
            <label className="block text-xs text-gray-500 mb-1">Suite</label>
            <select
              value={suiteId}
              onChange={(e) => setSuiteId(e.target.value)}
              className="w-full bg-gray-950 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300 focus:outline-none focus:border-indigo-500"
            >
              <option value="">Select a suite...</option>
              {suites?.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>
          <div className="flex-1 min-w-[180px]">
            <label className="block text-xs text-gray-500 mb-1">Dataset</label>
            <select
              value={datasetId}
              onChange={(e) => setDatasetId(e.target.value)}
              className="w-full bg-gray-950 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300 focus:outline-none focus:border-indigo-500"
            >
              <option value="">Select a dataset...</option>
              {datasets?.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.entry_count} entries)
                </option>
              ))}
            </select>
          </div>
          <button
            onClick={handleStart}
            disabled={!suiteId || !datasetId || startRun.isPending}
            className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-medium rounded-lg transition-colors"
          >
            {startRun.isPending ? "Starting..." : "Run Evaluation"}
          </button>
        </div>
        {startRun.isSuccess && (
          <p className="mt-3 text-sm text-emerald-400">
            Run started!{" "}
            <Link
              to={`/runs/${startRun.data.id}`}
              className="underline hover:text-emerald-300"
            >
              View results
            </Link>
          </p>
        )}
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <div className="px-5 py-3 border-b border-gray-800">
          <h2 className="text-sm font-medium text-gray-300">All Runs</h2>
        </div>
        {isLoading ? (
          <p className="p-5 text-gray-500 text-sm">Loading...</p>
        ) : !runs?.length ? (
          <p className="p-5 text-gray-500 text-sm">No runs yet.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-gray-500 text-left text-xs uppercase tracking-wider">
                <th className="px-5 py-2">ID</th>
                <th className="px-5 py-2">Suite</th>
                <th className="px-5 py-2">Dataset</th>
                <th className="px-5 py-2">Status</th>
                <th className="px-5 py-2 text-right">Score</th>
                <th className="px-5 py-2">Date</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((r) => (
                <tr
                  key={r.id}
                  className="border-t border-gray-800/50 hover:bg-gray-800/30"
                >
                  <td className="px-5 py-3">
                    <Link
                      to={`/runs/${r.id}`}
                      className="text-indigo-400 hover:underline font-mono text-xs"
                    >
                      {r.id.slice(0, 8)}...
                    </Link>
                  </td>
                  <td className="px-5 py-3 text-gray-300">{r.suite_name}</td>
                  <td className="px-5 py-3 text-gray-300">{r.dataset_name}</td>
                  <td className="px-5 py-3">
                    <StatusBadge status={r.status} />
                  </td>
                  <td className="px-5 py-3 text-right font-mono">
                    {r.overall_score != null ? r.overall_score.toFixed(2) : "-"}
                  </td>
                  <td className="px-5 py-3 text-gray-500">
                    {new Date(r.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
