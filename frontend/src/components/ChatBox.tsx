import { useState } from "react";
import { api } from "../api";

// "Is this healthy?" / "How much protein?" — grounded with the current nutrition context.
export function ChatBox({ nutrition }: { nutrition?: unknown }) {
  const [q, setQ] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);
  const [provider, setProvider] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function ask() {
    if (!q.trim()) return;
    setBusy(true);
    try {
      const res = await api.chat(q, nutrition);
      setAnswer(res.answer);
      setProvider(res.provider);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="rounded-xl border bg-white p-4 shadow-sm">
      <h2 className="mb-2 font-semibold">💬 Ask about this product</h2>
      <div className="flex gap-2">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && ask()}
          placeholder="Is this healthy? How much protein?"
          className="flex-1 rounded-lg border px-3 py-2 text-sm"
        />
        <button
          onClick={ask}
          disabled={busy}
          className="rounded-lg bg-slate-800 px-4 text-sm font-medium text-white disabled:opacity-50"
        >
          {busy ? "…" : "Ask"}
        </button>
      </div>
      {answer && (
        <p className="mt-3 text-sm">
          {answer}
          {provider && <span className="ml-2 text-xs text-slate-400">({provider})</span>}
        </p>
      )}
    </div>
  );
}
