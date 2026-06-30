"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { login } from "@/lib/api";
import { ErrorState } from "@/components/ErrorState";
import type { UserRole } from "@/lib/types";

export default function LoginPage() {
  const router = useRouter();
  const [loginAs, setLoginAs] = useState<UserRole>("doctor");
  const [email, setEmail] = useState("rupa.kapale@clinic.com");
  const [password, setPassword] = useState("Doctor@12345");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      await login(email, password, loginAs);
      router.replace("/dashboard");
    } catch (loginError) {
      setError(loginError instanceof Error ? loginError.message : "Unable to sign in");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-4 py-8">
      <section className="w-full max-w-md rounded border border-clinic-line bg-white p-5 shadow-soft sm:p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-semibold text-clinic-ink">Clinic Console</h1>
          <p className="mt-1 text-sm text-clinic-muted">Sign in to continue</p>
        </div>
        {error ? <div className="mb-4"><ErrorState message={error} /></div> : null}
        <form className="space-y-4" onSubmit={handleSubmit}>
          <fieldset>
            <legend className="text-sm font-semibold text-clinic-ink">Login As</legend>
            <div className="mt-2 grid grid-cols-2 gap-2">
              {[
                ["doctor", "Doctor"],
                ["receptionist", "Receptionist"]
              ].map(([value, label]) => (
                <label key={value} className={`flex min-h-12 items-center justify-center rounded border px-3 font-semibold ${loginAs === value ? "border-clinic-teal bg-clinic-mint text-clinic-ink" : "border-clinic-line bg-white text-clinic-muted"}`}>
                  <input
                    type="radio"
                    name="login-as"
                    value={value}
                    checked={loginAs === value}
                    onChange={() => setLoginAs(value as UserRole)}
                    className="sr-only"
                  />
                  {label}
                </label>
              ))}
            </div>
          </fieldset>
          <label className="block">
            <span className="text-sm font-semibold text-clinic-ink">Email</span>
            <input
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="mt-2 min-h-12 w-full rounded border border-clinic-line px-3 text-base"
            />
          </label>
          <label className="block">
            <span className="text-sm font-semibold text-clinic-ink">Password</span>
            <input
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="mt-2 min-h-12 w-full rounded border border-clinic-line px-3 text-base"
            />
          </label>
          <button type="submit" disabled={loading} className="min-h-12 w-full rounded bg-clinic-teal px-4 py-2 font-semibold text-white disabled:opacity-60">
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>
      </section>
    </main>
  );
}
