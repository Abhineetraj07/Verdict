export default function ScoreBar({
  score,
  max = 5,
}: {
  score: number;
  max?: number;
}) {
  const pct = Math.min((score / max) * 100, 100);
  const color =
    pct >= 60 ? "bg-emerald-500" : pct >= 40 ? "bg-amber-500" : "bg-red-500";

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-sm font-mono w-10 text-right">{score.toFixed(2)}</span>
    </div>
  );
}
