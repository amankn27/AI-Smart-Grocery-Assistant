// Thin API client. In dev, "/api" is proxied to the backend by Vite; in production set
// VITE_API_BASE to the backend's public URL at build time (see docs/deployment.md).
const BASE = (import.meta.env.VITE_API_BASE as string | undefined) || "/api";

// --- Auth token (persisted) ---
let authToken: string | null = typeof localStorage !== "undefined" ? localStorage.getItem("token") : null;

export function setAuthToken(token: string | null) {
  authToken = token;
  if (typeof localStorage === "undefined") return;
  if (token) localStorage.setItem("token", token);
  else localStorage.removeItem("token");
}

export function getAuthToken() {
  return authToken;
}

function authHeaders(): Record<string, string> {
  return authToken ? { Authorization: `Bearer ${authToken}` } : {};
}

export interface Detection {
  label: string;
  confidence: number;
  bbox_xyxy: number[];
  needs_confirmation: boolean;
}
export interface DetectResponse {
  model: string;
  width: number;
  height: number;
  detections: Detection[];
}

export interface NutritionField {
  value: number | null;
  unit: string | null;
  confidence: number;
}
export interface OcrResponse {
  engine: string;
  text: string;
  mean_confidence: number;
  nutrition: {
    basis: string;
    fields: Record<string, NutritionField>;
    low_confidence_fields: string[];
  };
}

export interface CartItem {
  product_id: string;
  name: string;
  mrp: number;
  quantity: number;
  category?: string | null;
  line_total: string;
}
export interface Cart {
  session_id: string;
  items: CartItem[];
  subtotal: string;
  total_gst: string;
  total: string;
  item_count: number;
}

async function postJSON<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${path} failed: ${res.status}`);
  return res.json();
}

async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { headers: authHeaders() });
  if (!res.ok) throw new Error(`${path} failed: ${res.status}`);
  return res.json();
}

async function del(path: string): Promise<void> {
  const res = await fetch(`${BASE}${path}`, { method: "DELETE", headers: authHeaders() });
  if (!res.ok && res.status !== 204) throw new Error(`${path} failed: ${res.status}`);
}

async function postForm<T>(path: string, file: Blob): Promise<T> {
  const fd = new FormData();
  fd.append("image", file, "frame.jpg");
  const res = await fetch(`${BASE}${path}`, { method: "POST", body: fd });
  if (!res.ok) throw new Error(`${path} failed: ${res.status}`);
  return res.json();
}

export interface Product {
  product_id: string;
  name: string;
  brand: string;
  barcode: string;
  category: string;
  mrp: number;
  nutrition: Record<string, number>;
}
export interface BarcodeResponse {
  decoder: string;
  barcodes: { value: string; type: string }[];
  matched_barcode?: string | null;
  product: Product | null;
  fallback: string | null;
}
export interface RecommendResponse {
  target: { product_id: string; name: string; category: string };
  alternatives: (Product & { health_score: number; score_delta: number })[];
  explanation: string;
  explanation_provider: string;
  sources: { id: string; score: number }[];
}

export interface ValueMetric {
  product_id: string;
  name: string;
  brand: string;
  mrp: number;
  health_score: number;
  health_per_rupee: number | null;
}
export interface ValueResponse {
  target: ValueMetric;
  category: string;
  category_size: number;
  price_percentile: number | null;
  cheapest: ValueMetric | null;
  best_value: ValueMetric | null;
  target_is_cheapest: boolean;
  target_is_best_value: boolean;
}
export interface DietPlan {
  target_kcal: number;
  total_kcal: number;
  total_protein_g: number;
  kcal_gap: number;
  meets_protein: boolean;
  items: { product_id: string; name: string; energy_kcal: number; protein_g: number; health_score: number }[];
  narrative: string;
  narrative_provider: string;
}

export interface Tokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}
export interface PantryItem {
  id: number;
  name: string;
  category: string;
  quantity: number;
  expiry_date: string | null;
  days_left: number | null;
  status: "expired" | "expiring_soon" | "fresh" | "no_date";
}
export interface DashboardData {
  total_spend: string;
  total_items: number;
  total_calories: number;
  average_health_score: number | null;
  scan_count: number;
  category_mix: { category: string; items: number; spend: string }[];
}

export const api = {
  detect: (frame: Blob) => postForm<DetectResponse>("/detect", frame),
  ocr: (frame: Blob) => postForm<OcrResponse>("/ocr", frame),
  scanBarcode: (frame: Blob) => postForm<BarcodeResponse>("/barcode", frame),
  recommend: (product_id: string, limit = 3) =>
    postJSON<RecommendResponse>("/recommend", { product_id, limit }),
  recipe: (opts: { session_id?: string; diet?: string; servings?: number }) =>
    postJSON<{ ingredients: string[]; recipe_text: string; provider: string }>("/recipe", opts),
  value: (product_id: string) => postJSON<ValueResponse>("/value", { product_id }),
  dietPlan: (opts: { target_kcal: number; min_protein_g?: number; diet?: string }) =>
    postJSON<DietPlan>("/diet/plan", opts),
  voice: async (audio: Blob) => {
    const fd = new FormData();
    fd.append("audio", audio, "speech.webm");
    const res = await fetch(`${BASE}/voice`, { method: "POST", body: fd });
    return res.json() as Promise<{
      transcript: string;
      answer: string;
      stt_engine: string;
      tts_engine?: string;
      audio_base64?: string | null;
      audio_mime?: string;
      fallback?: string;
      hint?: string;
    }>;
  },
  voiceText: async (text: string) => {
    const fd = new FormData();
    fd.append("text", text);
    const res = await fetch(`${BASE}/voice`, { method: "POST", body: fd });
    return res.json();
  },
  analyze: (nutrition: Record<string, number>) => postJSON("/analyze", nutrition),
  chat: (question: string, context?: unknown) =>
    postJSON<{ answer: string; provider: string }>("/chat", { question, context }),
  addToCart: (item: Omit<CartItem, "line_total">) => postJSON<Cart>("/cart/add", item),
  getCart: async (): Promise<Cart> => {
    const res = await fetch(`${BASE}/cart`);
    return res.json();
  },

  // --- Auth ---
  register: (email: string, password: string) => postJSON<Tokens>("/auth/register", { email, password }),
  login: async (email: string, password: string): Promise<Tokens> => {
    // OAuth2PasswordRequestForm expects form-encoded username/password.
    const body = new URLSearchParams({ username: email, password });
    const res = await fetch(`${BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });
    if (!res.ok) throw new Error("Invalid credentials");
    return res.json();
  },
  me: () => getJSON<{ id: number; email: string; created_at: string }>("/auth/me"),

  // --- Pantry (auth) ---
  pantryList: () => getJSON<{ items: PantryItem[] }>("/pantry"),
  pantryReminders: (withinDays = 3) =>
    getJSON<{ within_days: number; reminders: PantryItem[] }>(`/pantry/reminders?within_days=${withinDays}`),
  pantryAdd: (item: { name: string; category?: string; quantity?: number; expiry_date?: string | null }) =>
    postJSON<{ id: number }>("/pantry", item),
  pantryDelete: (id: number) => del(`/pantry/${id}`),

  // --- History (auth) ---
  recordScan: (scan: {
    product_id?: string;
    name?: string;
    brand?: string;
    category?: string;
    mrp?: number;
    quantity?: number;
    nutrition?: Record<string, number>;
  }) => postJSON<{ id: number; health_score: number }>("/history/scan", scan),

  // --- Dashboard (auth) ---
  dashboard: () => getJSON<DashboardData>("/dashboard"),
};
