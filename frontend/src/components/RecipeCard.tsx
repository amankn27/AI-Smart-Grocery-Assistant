import { useState } from "react";
import { api } from "../api";

// Generates a recipe from the current cart contents.
export function RecipeCard() {
  const [data, setData] = useState<{ ingredients: string[]; recipe_text: string; provider: string } | null>(null);
  const [diet, setDiet] = useState("any");
  const [busy, setBusy] = useState(false);

  async function generate() {
    setBusy(true);
    try {
      setData(await api.recipe({ session_id: "demo", diet, servings: 2 }));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="rounded-xl border bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between gap-2">
        <h2 className="font-semibold">👩‍🍳 Recipe from cart</h2>
        <div className="flex items-center gap-2">
          <select
            value={diet}
            onChange={(e) => setDiet(e.target.value)}
            className="rounded-lg border px-2 py-1 text-sm"
          >
            <option value="any">Any</option>
            <option value="veg">Veg</option>
            <option value="non-veg">Non-veg</option>
            <option value="vegan">Vegan</option>
          </select>
          <button
            onClick={generate}
            disabled={busy}
            className="rounded-lg bg-emerald-600 px-3 py-1 text-sm font-medium text-white disabled:opacity-50"
          >
            {busy ? "…" : "Generate"}
          </button>
        </div>
      </div>
      {data && (
        <div className="mt-3 text-sm">
          <p className="text-slate-500">Ingredients: {data.ingredients.join(", ") || "—"}</p>
          <pre className="mt-2 whitespace-pre-wrap font-sans">{data.recipe_text}</pre>
          <p className="mt-1 text-xs text-slate-400">({data.provider})</p>
        </div>
      )}
    </div>
  );
}
