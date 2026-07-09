import { useQuery } from "@tanstack/react-query";
import { api } from "../api";
import { useAuth } from "../auth";

// Spend / calories / avg-health summary + a CSS-bar category mix (no chart dependency).
export function Dashboard() {
  const { email } = useAuth();
  const { data } = useQuery({ queryKey: ["dashboard"], queryFn: api.dashboard, enabled: !!email });

  if (!email) {
    return <p className="rounded-xl border bg-white p-4 text-sm text-slate-500 shadow-sm">Log in to see your dashboard.</p>;
  }
  if (!data) return null;

  const maxItems = Math.max(1, ...data.category_mix.map((c) => c.items));
  const grade = data.average_health_score;

  return (
    <div className="rounded-xl border bg-white p-4 shadow-sm">
      <h2 className="mb-3 font-semibold">📊 Dashboard</h2>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat label="Spend" value={`₹${data.total_spend}`} />
        <Stat label="Items" value={String(data.total_items)} />
        <Stat label="Calories" value={`${Math.round(data.total_calories)}`} />
        <Stat label="Avg health" value={grade === null ? "—" : `${grade}/100`} />
      </div>

      {data.category_mix.length > 0 && (
        <div className="mt-4">
          <h3 className="mb-2 text-sm font-medium text-slate-500">Category mix</h3>
          <ul className="space-y-1">
            {data.category_mix.map((c) => (
              <li key={c.category} className="flex items-center gap-2 text-sm">
                <span className="w-28 shrink-0 truncate text-slate-600">{c.category}</span>
                <div className="h-4 flex-1 rounded bg-slate-100">
                  <div
                    className="h-4 rounded bg-emerald-500"
                    style={{ width: `${(c.items / maxItems) * 100}%` }}
                  />
                </div>
                <span className="w-20 shrink-0 text-right text-slate-500">
                  {c.items} · ₹{c.spend}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
      {data.scan_count === 0 && (
        <p className="mt-3 text-sm text-slate-400">No scans recorded yet. Scan products to populate your dashboard.</p>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border p-3">
      <div className="text-xs text-slate-500">{label}</div>
      <div className="text-lg font-bold">{value}</div>
    </div>
  );
}
