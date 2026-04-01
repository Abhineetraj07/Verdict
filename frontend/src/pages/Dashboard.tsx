import { Link } from "react-router-dom";
import { useRuns, useSuites, useDatasets } from "../api/hooks";
import StatusBadge from "../components/StatusBadge";

export default function Dashboard() {
  const { data: runs, isLoading: runsLoading } = useRuns();
  const { data: suites } = useSuites();
  const { data: datasets } = useDatasets();

  const completed = runs?.filter((r) => r.status === "completed") ?? [];
  const avgScore =
    completed.length > 0
      ? completed.reduce((s, r) => s + (r.overall_score ?? 0), 0) /
        completed.length
      : 0;

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-gray-500 text-sm mt-1">
            Overview of your evaluation runs
          </p>
        </div>
        <Link
          to="/runs"
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-lg transition-colors"
        >
          New Run
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <StatCard label="Total Runs" value={runs?.length ?? 0} />
        <StatCard label="Completed" value={completed.length} />
        <StatCard label="Suites" value={suites?.length ?? 0} />
        <StatCard label="Datasets" value={datasets?.length ?? 0} />
      </div>

      {avgScore > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 mb-8">
          <p className="text-sm text-gray-400 mb-1">
            Average Score (completed runs)
          </p>
          <p className="text-3xl font-bold text-white">{avgScore.toFixed(2)}</p>
        </div>
      )}

      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <div className="px-5 py-3 border-b border-gray-800">
          <h2 className="text-sm font-medium text-gray-300">Recent Runs</h2>
        </div>
        {runsLoading ? (
          <p className="p-5 text-gray-500 text-sm">Loading...</p>
        ) : !runs?.length ? (
          <p className="p-5 text-gray-500 text-sm">
            No runs yet.{" "}
            <Link to="/runs" className="text-indigo-400 hover:underline">
              Start one
            </Link>
          </p>
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
              {runs.slice(0, 10).map((r) => (
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

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <p className="text-xs text-gray-500 uppercase tracking-wider">{label}</p>
      <p className="text-2xl font-bold text-white mt-1">{value}</p>
    </div>
  );
}
