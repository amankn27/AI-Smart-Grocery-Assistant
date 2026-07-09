// Thin API client. All calls go through the Vite proxy at /api → FastAPI backend.
const BASE = "/api";

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
