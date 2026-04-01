import { useState } from "react";
import { useDatasets, useCreateDataset } from "../api/hooks";
import type { DatasetCreate } from "../api/types";

export default function Datasets() {
  const { data: datasets, isLoading } = useDatasets();
  const createDataset = useCreateDataset();
  const [showForm, setShowForm] = useState(false);
  const [jsonInput, setJsonInput] = useState("");

  const handleCreate = () => {
    try {
      const parsed: DatasetCreate = JSON.parse(jsonInput);
      createDataset.mutate(parsed, {
        onSuccess: () => {
          setJsonInput("");
          setShowForm(false);
        },
      });
    } catch {
      alert("Invalid JSON.");
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Datasets</h1>
          <p className="text-gray-500 text-sm mt-1">
            Manage test datasets for evaluation
          </p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-lg transition-colors"
        >
          {showForm ? "Cancel" : "New Dataset"}
        </button>
      </div>

      {showForm && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 mb-6">
          <p className="text-sm text-gray-400 mb-2">Paste dataset as JSON:</p>
          <textarea
            value={jsonInput}
            onChange={(e) => setJsonInput(e.target.value)}
            placeholder='{"name": "...", "entries": [{"input": "...", "output": "..."}]}'
            className="w-full h-48 bg-gray-950 border border-gray-700 rounded-lg p-3 text-sm font-mono text-gray-300 focus:outline-none focus:border-indigo-500"
          />
          <button
            onClick={handleCreate}
            disabled={createDataset.isPending}
            className="mt-3 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm font-medium rounded-lg"
          >
            {createDataset.isPending ? "Creating..." : "Create Dataset"}
          </button>
        </div>
      )}

      {isLoading ? (
        <p className="text-gray-500">Loading...</p>
      ) : !datasets?.length ? (
        <p className="text-gray-500 text-sm">No datasets yet.</p>
      ) : (
        <div className="space-y-3">
          {datasets.map((d) => (
            <div
              key={d.id}
              className="bg-gray-900 border border-gray-800 rounded-xl p-5"
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-white font-medium">{d.name}</h3>
                </div>
                <span className="text-xs text-gray-600 font-mono">
                  {d.id.slice(0, 8)}...
                </span>
              </div>
              <p className="mt-2 text-xs text-gray-400">
                {d.entry_count} entries
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
