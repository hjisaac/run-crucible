const STATUS_STYLES = {
  pending: "bg-yellow-400/15 text-yellow-300 ring-yellow-400/30",
  running: "bg-blue-400/15 text-blue-300 ring-blue-400/30 animate-pulse",
  completed: "bg-green-400/15 text-green-300 ring-green-400/30",
  failed: "bg-red-400/15 text-red-300 ring-red-400/30",
};

export function StatusBadge({ status }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${STATUS_STYLES[status] ?? "bg-slate-400/15 text-slate-300 ring-slate-400/30"}`}
    >
      {status}
    </span>
  );
}
