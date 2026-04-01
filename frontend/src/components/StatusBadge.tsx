const colors: Record<string, string> = {
  completed: "bg-emerald-500/20 text-emerald-400",
  running: "bg-amber-500/20 text-amber-400",
  pending: "bg-gray-500/20 text-gray-400",
  failed: "bg-red-500/20 text-red-400",
};

export default function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
        colors[status] ?? colors.pending
      }`}
    >
      {status === "running" && (
        <span className="mr-1.5 h-1.5 w-1.5 rounded-full bg-amber-400 animate-pulse" />
      )}
      {status}
    </span>
  );
}
