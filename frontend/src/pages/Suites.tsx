import { useState } from "react";
import yaml from "js-yaml";
import { useSuites, useCreateSuite } from "../api/hooks";
import type { EvalSuiteCreate } from "../api/types";

const EXAMPLE_YAML = `name: "My Eval Suite"
description: "Evaluate LLM outputs"
judges:
  - name: "accuracy_judge"
    dimension: "accuracy"
    rubric: |
      Score on accuracy (1-5):
      5: Completely accurate
      4: Mostly accurate
      3: Partially accurate
      2: Mostly inaccurate
      1: Completely wrong
    scoring_scale: 5
    weight: 0.5
  - name: "clarity_judge"
    dimension: "clarity"
    rubric: |
      Score on clarity (1-5):
      5: Crystal clear
      4: Mostly clear
      3: Somewhat clear
      2: Confusing
      1: Incomprehensible
    scoring_scale: 5
    weight: 0.5
aggregation:
  method: "weighted_average"`;

function parseInput(text: string): EvalSuiteCreate {
  const trimmed = text.trim();
  // Try JSON first
  if (trimmed.startsWith("{")) {
    return JSON.parse(trimmed);
  }
  // Otherwise treat as YAML
  return yaml.load(trimmed) as EvalSuiteCreate;
}

export default function Suites() {
  const { data: suites, isLoading } = useSuites();
  const createSuite = useCreateSuite();
  const [showForm, setShowForm] = useState(false);
  const [input, setInput] = useState("");
  const [error, setError] = useState("");

  const handleCreate = () => {
    setError("");
    try {
      const parsed = parseInput(input);
      if (!parsed.name || !parsed.judges?.length) {
        setError("Suite must have a name and at least one judge.");
        return;
      }
      createSuite.mutate(parsed, {
        onSuccess: () => {
          setInput("");
          setShowForm(false);
        },
      });
    } catch (e) {
      setError(`Invalid config. Paste valid JSON or YAML. (${e instanceof Error ? e.message : e})`);
    }
  };

  const loadExample = () => {
    setInput(EXAMPLE_YAML);
    setError("");
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Eval Suites</h1>
          <p className="text-gray-500 text-sm mt-1">
            Configure judge panels and aggregation
          </p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-lg transition-colors"
        >
          {showForm ? "Cancel" : "New Suite"}
        </button>
      </div>

      {showForm && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 mb-6">
          <p className="text-sm text-gray-300 mb-1">
            Paste suite config (YAML or JSON):
          </p>
          <p className="text-xs text-gray-500 mb-3">
            Must include: name, judges (with dimension, rubric, weight, scoring_scale), and aggregation method.
          </p>
          <textarea
            value={input}
            onChange={(e) => { setInput(e.target.value); setError(""); }}
            placeholder={`name: "My Suite"\ndescription: "..."\njudges:\n  - name: "judge_1"\n    dimension: "accuracy"\n    rubric: "Score on accuracy (1-5)..."\n    scoring_scale: 5\n    weight: 1.0\naggregation:\n  method: "weighted_average"`}
            className="w-full h-72 bg-gray-950 border border-gray-700 rounded-lg p-3 text-sm font-mono text-gray-300 focus:outline-none focus:border-indigo-500"
          />
          {error && (
            <p className="mt-2 text-sm text-red-400">{error}</p>
          )}
          <div className="mt-3 flex items-center gap-3">
            <button
              onClick={handleCreate}
              disabled={createSuite.isPending || !input.trim()}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm font-medium rounded-lg"
            >
              {createSuite.isPending ? "Creating..." : "Create Suite"}
            </button>
            <button
              onClick={loadExample}
              className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 text-sm rounded-lg transition-colors"
            >
              Load Example
            </button>
          </div>
        </div>
      )}

      {isLoading ? (
        <p className="text-gray-500">Loading...</p>
      ) : !suites?.length ? (
        <p className="text-gray-500 text-sm">
          No suites yet. Create one to get started.
        </p>
      ) : (
        <div className="space-y-3">
          {suites.map((s) => (
            <div
              key={s.id}
              className="bg-gray-900 border border-gray-800 rounded-xl p-5"
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-white font-medium">{s.name}</h3>
                  <p className="text-gray-500 text-sm mt-0.5">
                    {s.description}
                  </p>
                </div>
                <span className="text-xs text-gray-600 font-mono">
                  {s.id.slice(0, 8)}...
                </span>
              </div>
              <div className="mt-3 flex gap-4 text-xs text-gray-400">
                <span>
                  {s.judges.length} judge{s.judges.length !== 1 ? "s" : ""}
                </span>
                <span>
                  Dimensions:{" "}
                  {s.judges.map((j) => j.dimension).join(", ")}
                </span>
                <span>Aggregation: {s.aggregation.method}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
