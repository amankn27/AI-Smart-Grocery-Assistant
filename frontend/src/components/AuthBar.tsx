import { useState } from "react";
import { useAuth } from "../auth";

// Compact login/register control shown in the header. Toggles between signed-in (email +
// logout) and a small email/password form.
export function AuthBar() {
  const { email, login, register, logout } = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (email) {
    return (
      <div className="flex items-center gap-3 text-sm">
        <span className="text-slate-500">{email}</span>
        <button onClick={logout} className="rounded-lg border px-3 py-1 font-medium">
          Log out
        </button>
      </div>
    );
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      if (mode === "login") await login(form.email, form.password);
      else await register(form.email, form.password);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="flex flex-wrap items-center gap-2 text-sm">
      <input
        type="email"
        required
        placeholder="email"
        value={form.email}
        onChange={(e) => setForm({ ...form, email: e.target.value })}
        className="w-40 rounded-lg border px-2 py-1"
      />
      <input
        type="password"
        required
        minLength={6}
        placeholder="password"
        value={form.password}
        onChange={(e) => setForm({ ...form, password: e.target.value })}
        className="w-32 rounded-lg border px-2 py-1"
      />
      <button disabled={busy} className="rounded-lg bg-slate-800 px-3 py-1 font-medium text-white disabled:opacity-50">
        {mode === "login" ? "Log in" : "Sign up"}
      </button>
      <button
        type="button"
        onClick={() => setMode(mode === "login" ? "register" : "login")}
        className="text-slate-500 underline"
      >
        {mode === "login" ? "need an account?" : "have an account?"}
      </button>
      {error && <span className="text-red-600">{error}</span>}
    </form>
  );
}
