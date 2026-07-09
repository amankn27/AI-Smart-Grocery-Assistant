import { useState } from "react";
import { api, type DietPlan } from "../api";

// Builds a deterministic catalog basket toward a calorie/protein target and shows the LLM
// narrative. No auth required.
export function DietPlanner() {
  const [targetKcal, setTargetKcal] = useState(1200);
  const [minProtein, setMinProtein] = useState(40);
  const [diet, setDiet] = useState("any");
  const [plan, setPlan] = useState<DietPlan | null>(null);
  const [busy, setBusy] = useState(false);

  async function generate() {
    setBusy(true);
    try {
      setPlan(await api.dietPlan({ target_kcal: targetKcal, min_protein_g: minProtein, diet }));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="rounded-xl border bg-white p-4 shadow-sm">
      <h2 className="mb-3 font-semibold">🍽️ Diet planner</h2>

      <div className="mb-4 flex flex-wrap items-end gap-3 text-sm">
        <label className="flex flex-col">
          <span className="text-slate-500">Target kcal</span>
          <input
            type="number"
            min={200}
            max={6000}
            value={targetKcal}
            onChange={(e) => setTargetKcal(Number(e.target.value))}
            className="w-28 rounded-lg border px-2 py-1"
          />
        </label>
        <label className="flex flex-col">
          <span className="text-slate-500">Min protein (g)</span>
          <input
            type="number"
            min={0}
            value={minProtein}
            onChange={(e) => setMinProtein(Number(e.target.value))}
            className="w-28 rounded-lg border px-2 py-1"
          />
        </label>
        <label className="flex flex-col">
          <span className="text-slate-500">Diet</span>
          <select value={diet} onChange={(e) => setDiet(e.target.value)} className="rounded-lg border px-2 py-1">
            <option value="any">Any</option>
            <option value="veg">Veg</option>
            <option value="non-veg">Non-veg</option>
            <option value="vegan">Vegan</option>
          </select>
        </label>
        <button
          onClick={generate}
          disabled={busy}
          className="rounded-lg bg-emerald-600 px-4 py-2 font-medium text-white disabled:opacity-50"
        >
          {busy ? "…" : "Plan"}
        </button>
      </div>

      {plan && (
        <div className="text-sm">
          <div className="mb-2 flex flex-wrap gap-3">
            <span className="rounded-full bg-slate-100 px-3 py-1">≈{Math.round(plan.total_kcal)} kcal</span>
            <span className="rounded-full bg-slate-100 px-3 py-1">{Math.round(plan.total_protein_g)} g protein</span>
            <span className={`rounded-full px-3 py-1 ${plan.meets_protein ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"}`}>
              {plan.meets_protein ? "protein goal met" : "under protein goal"}
            </span>
          </div>
          <ul className="mb-3 grid grid-cols-1 gap-1 sm:grid-cols-2">
            {plan.items.map((i) => (
              <li key={i.product_id} className="flex justify-between rounded border p-2">
                <span className="truncate">{i.name}</span>
                <span className="text-slate-500">{Math.round(i.energy_kcal)} kcal · {i.health_score}/100</span>
              </li>
            ))}
          </ul>
          {plan.narrative && <p className="whitespace-pre-wrap text-slate-600">{plan.narrative}</p>}
        </div>
      )}
    </div>
  );
}
