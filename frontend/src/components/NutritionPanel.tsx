import { useQuery } from "@tanstack/react-query";
import { api, type OcrResponse } from "../api";

// Shows parsed nutrition fields (dimming low-confidence ones) and the deterministic health
// score/warnings from /analyze.
export function NutritionPanel({ ocr }: { ocr: OcrResponse | null }) {
  const nutritionValues: Record<string, number> = {};
  if (ocr) {
    for (const [k, f] of Object.entries(ocr.nutrition.fields)) {
      if (f.value != null && f.confidence >= 0.5) nutritionValues[k] = f.value;
    }
  }

  const { data: analysis } = useQuery({
    queryKey: ["analyze", nutritionValues],
    queryFn: () => api.analyze(nutritionValues),
    enabled: Object.keys(nutritionValues).length > 0,
  });

  if (!ocr) return null;

  const gradeColor: Record<string, string> = {
    A: "bg-emerald-500", B: "bg-lime-500", C: "bg-yellow-500", D: "bg-orange-500", E: "bg-red-500",
  };
  const a = analysis as any;

  return (
    <div className="rounded-xl border bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="font-semibold">Nutrition (per 100g · {ocr.nutrition.basis})</h2>
        {a && (
          <span className={`rounded-full px-3 py-1 text-sm font-bold text-white ${gradeColor[a.grade]}`}>
            {a.grade} · {a.score}/100
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 gap-2 text-sm sm:grid-cols-4">
        {Object.entries(ocr.nutrition.fields).map(([k, f]) => (
          <div key={k} className={`rounded border p-2 ${f.confidence < 0.5 ? "opacity-40" : ""}`}>
            <div className="text-slate-500">{k.replace(/_/g, " ")}</div>
            <div className="font-medium">
              {f.value ?? "—"} {f.unit ?? ""}
            </div>
          </div>
        ))}
      </div>

      {a?.warnings?.length > 0 && (
        <ul className="mt-3 space-y-1 text-sm">
          {a.warnings.map((w: any, i: number) => (
            <li key={i} className={w.severity === "red" ? "text-red-600" : "text-amber-600"}>
              ⚠ {w.message}
            </li>
          ))}
        </ul>
      )}
      {a?.positives?.length > 0 && (
        <ul className="mt-1 space-y-1 text-sm text-emerald-600">
          {a.positives.map((p: string, i: number) => (
            <li key={i}>✓ {p}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
