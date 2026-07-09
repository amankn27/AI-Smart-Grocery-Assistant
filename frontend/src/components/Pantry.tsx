import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type PantryItem } from "../api";
import { useAuth } from "../auth";

const STATUS_STYLE: Record<PantryItem["status"], { label: string; cls: string }> = {
  expired: { label: "Expired", cls: "bg-red-100 text-red-700" },
  expiring_soon: { label: "Expiring soon", cls: "bg-amber-100 text-amber-700" },
  fresh: { label: "Fresh", cls: "bg-emerald-100 text-emerald-700" },
  no_date: { label: "No date", cls: "bg-slate-100 text-slate-500" },
};

export function Pantry() {
  const { email } = useAuth();
  const qc = useQueryClient();
  const [form, setForm] = useState({ name: "", category: "", quantity: 1, expiry_date: "" });

  const { data } = useQuery({
    queryKey: ["pantry"],
    queryFn: api.pantryList,
    enabled: !!email,
  });

  if (!email) {
    return <p className="rounded-xl border bg-white p-4 text-sm text-slate-500 shadow-sm">Log in to manage your pantry.</p>;
  }

  async function add(e: React.FormEvent) {
    e.preventDefault();
    if (!form.name.trim()) return;
    await api.pantryAdd({
      name: form.name,
      category: form.category || undefined,
      quantity: form.quantity,
      expiry_date: form.expiry_date || null,
    });
    setForm({ name: "", category: "", quantity: 1, expiry_date: "" });
    qc.invalidateQueries({ queryKey: ["pantry"] });
  }

  async function remove(id: number) {
    await api.pantryDelete(id);
    qc.invalidateQueries({ queryKey: ["pantry"] });
  }

  const items = data?.items ?? [];
  const reminders = items.filter((i) => i.status === "expired" || i.status === "expiring_soon");

  return (
    <div className="rounded-xl border bg-white p-4 shadow-sm">
      <h2 className="mb-3 font-semibold">🧺 Pantry</h2>

      {reminders.length > 0 && (
        <div className="mb-3 rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-800">
          ⏰ {reminders.length} item{reminders.length > 1 ? "s" : ""} need attention:{" "}
          {reminders.map((r) => r.name).join(", ")}
        </div>
      )}

      <form onSubmit={add} className="mb-4 flex flex-wrap items-end gap-2 text-sm">
        <input
          placeholder="item name"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          className="flex-1 rounded-lg border px-2 py-1"
        />
        <input
          placeholder="category"
          value={form.category}
          onChange={(e) => setForm({ ...form, category: e.target.value })}
          className="w-28 rounded-lg border px-2 py-1"
        />
        <input
          type="number"
          min={1}
          value={form.quantity}
          onChange={(e) => setForm({ ...form, quantity: Number(e.target.value) })}
          className="w-16 rounded-lg border px-2 py-1"
        />
        <input
          type="date"
          value={form.expiry_date}
          onChange={(e) => setForm({ ...form, expiry_date: e.target.value })}
          className="rounded-lg border px-2 py-1"
        />
        <button className="rounded-lg bg-emerald-600 px-3 py-1 font-medium text-white">Add</button>
      </form>

      {items.length === 0 ? (
        <p className="text-sm text-slate-400">Pantry is empty.</p>
      ) : (
        <ul className="divide-y text-sm">
          {items.map((i) => {
            const s = STATUS_STYLE[i.status];
            return (
              <li key={i.id} className="flex items-center justify-between py-2">
                <div>
                  <span className="font-medium">{i.name}</span>
                  <span className="ml-2 text-slate-400">×{i.quantity}</span>
                  {i.days_left !== null && (
                    <span className="ml-2 text-xs text-slate-400">
                      {i.days_left < 0 ? `${-i.days_left}d ago` : `${i.days_left}d left`}
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${s.cls}`}>{s.label}</span>
                  <button onClick={() => remove(i.id)} className="text-slate-400 hover:text-red-600">
                    ✕
                  </button>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
