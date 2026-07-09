import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { CameraCapture } from "./components/CameraCapture";
import { NutritionPanel } from "./components/NutritionPanel";
import { CartView } from "./components/Cart";
import { ChatBox } from "./components/ChatBox";
import { Recommendations } from "./components/Recommendations";
import { VoiceAssistant } from "./components/VoiceAssistant";
import { RecipeCard } from "./components/RecipeCard";
import { AuthBar } from "./components/AuthBar";
import { Pantry } from "./components/Pantry";
import { Dashboard } from "./components/Dashboard";
import { DietPlanner } from "./components/DietPlanner";
import { api, getAuthToken, type DetectResponse, type OcrResponse, type Product } from "./api";
import { useAuth } from "./auth";

type Tab = "scan" | "planner" | "pantry" | "dashboard";

export default function App() {
  const [tab, setTab] = useState<Tab>("scan");
  const { loading } = useAuth();

  return (
    <div className="mx-auto max-w-6xl p-4">
      <header className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">🛒 Smart Grocery Assistant</h1>
          <p className="text-sm text-slate-500">
            Identify products, read nutrition, score health, build the bill (INR + GST).
          </p>
        </div>
        {!loading && <AuthBar />}
      </header>

      <nav className="mb-4 flex gap-2">
        {(["scan", "planner", "pantry", "dashboard"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`rounded-lg px-4 py-1.5 text-sm font-medium capitalize ${
              tab === t ? "bg-slate-800 text-white" : "bg-white text-slate-600 border"
            }`}
          >
            {t}
          </button>
        ))}
      </nav>

      {tab === "scan" && <ScanView />}
      {tab === "planner" && <DietPlanner />}
      {tab === "pantry" && <Pantry />}
      {tab === "dashboard" && <Dashboard />}
    </div>
  );
}

// The Phase 0/1/2 scan workflow.
function ScanView() {
  const [detection, setDetection] = useState<DetectResponse | null>(null);
  const [ocr, setOcr] = useState<OcrResponse | null>(null);
  const [product, setProduct] = useState<Product | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const qc = useQueryClient();

  async function onFrame(frame: Blob) {
    setBusy(true);
    try {
      const [det, o] = await Promise.all([api.detect(frame), api.ocr(frame)]);
      setDetection(det);
      setOcr(o);
    } finally {
      setBusy(false);
    }
  }

  async function onBarcode(frame: Blob) {
    setBusy(true);
    setNotice(null);
    try {
      const res = await api.scanBarcode(frame);
      if (res.product) {
        setProduct(res.product);
        await api.addToCart({
          product_id: res.product.product_id,
          name: res.product.name,
          mrp: res.product.mrp,
          quantity: 1,
          category: res.product.category,
        });
        qc.invalidateQueries({ queryKey: ["cart"] });
        // Record a scan for history/dashboard when signed in (best-effort).
        if (getAuthToken()) {
          api
            .recordScan({
              product_id: res.product.product_id,
              name: res.product.name,
              brand: res.product.brand,
              category: res.product.category,
              mrp: res.product.mrp,
              quantity: 1,
              nutrition: res.product.nutrition,
            })
            .then(() => qc.invalidateQueries({ queryKey: ["dashboard"] }))
            .catch(() => undefined);
        }
        setNotice(`Added ${res.product.name} to cart.`);
      } else if (res.fallback === "not_in_catalog") {
        setNotice(`Barcode ${res.matched_barcode ?? res.barcodes[0]?.value} not in catalog — enter manually.`);
      } else {
        setNotice("No barcode detected — try again or use manual entry.");
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid gap-4 md:grid-cols-3">
      <section className="md:col-span-2 space-y-4">
        <CameraCapture onFrame={onFrame} onBarcode={onBarcode} detection={detection} busy={busy} />
        {notice && <p className="rounded-lg bg-slate-100 px-3 py-2 text-sm text-slate-700">{notice}</p>}
        <NutritionPanel ocr={ocr} />
        {product && <Recommendations productId={product.product_id} productName={product.name} />}
        <ChatBox nutrition={ocr?.nutrition} />
        <VoiceAssistant />
      </section>
      <aside className="space-y-4">
        <CartView />
        <RecipeCard />
      </aside>
    </div>
  );
}
