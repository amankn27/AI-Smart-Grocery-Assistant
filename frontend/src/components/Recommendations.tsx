import { useState } from "react";
import { api, type RecommendResponse, type ValueResponse } from "../api";

// Shows healthier same-category alternatives (deterministic ranking) plus the RAG-grounded
// explanation and a price/value summary. Triggered for a known catalog product.
export function Recommendations({ productId, productName }: { productId: string; productName: string }) {
  const [data, setData] = useState<RecommendResponse | null>(null);
  const [value, setValue] = useState<ValueResponse | null>(null);
  const [busy, setBusy] = useState(false);

  async function load() {
    setBusy(true);
    try {
      const [rec, val] = await Promise.all([api.recommend(productId, 3), api.value(productId)]);
      setData(rec);
      setValue(val);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="rounded-xl border bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold">🥗 Healthier options</h2>
        <button
          onClick={load}
          disabled={busy}
          className="rounded-lg bg-emerald-600 px-3 py-1 text-sm font-medium text-white disabled:opacity-50"
        >
          {busy ? "…" : `Find for ${productName}`}
        </button>
      </div>

      {value && (
        <div className="mt-3 rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-600">
          💰 In {value.category} ({value.category_size}):{" "}
          {value.cheapest && <>cheapest is <b>{value.cheapest.name}</b> (₹{value.cheapest.mrp}); </>}
          {value.best_value && <>best value is <b>{value.best_value.name}</b></>}
          {value.target_is_best_value && " — that's this one 👍"}
        </div>
      )}

      {data && (
        <div className="mt-3 space-y-3">
          {data.alternatives.length === 0 ? (
            <p className="text-sm text-slate-500">{data.explanation}</p>
          ) : (
            <>
              <ul className="space-y-2">
                {data.alternatives.map((a) => (
                  <li key={a.product_id} className="flex items-center justify-between rounded border p-2 text-sm">
                    <span>
                      {a.brand} {a.name}
                    </span>
                    <span className="rounded-full bg-emerald-100 px-2 py-0.5 font-medium text-emerald-700">
                      {a.health_score}/100 (+{a.score_delta})
                    </span>
                  </li>
                ))}
              </ul>
              <p className="text-sm text-slate-600">{data.explanation}</p>
              {data.sources.length > 0 && (
                <p className="text-xs text-slate-400">
                  Grounded in: {data.sources.map((s) => s.id).join(", ")} ({data.explanation_provider})
                </p>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
