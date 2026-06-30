"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, clearTokens, getAccessToken, resetDemoClinic, subscribeAuthChanges } from "@/lib/api";
import type { User, UserRole } from "@/lib/types";

const navItems = [
  { href: "/dashboard", label: "Dashboard", roles: ["admin", "doctor", "receptionist"] },
  { href: "/patients", label: "Patients", roles: ["admin", "doctor", "receptionist"] },
  { href: "/queue", label: "Queue", roles: ["admin", "doctor", "receptionist"] },
  { href: "/consultations/new", label: "New Consultation", roles: ["admin", "doctor", "receptionist"] },
  { href: "/operations", label: "Operations", roles: ["admin", "doctor", "receptionist"] },
  { href: "/payment", label: "Analytics & Finance", roles: ["admin", "doctor"] },
  { href: "/settings", label: "Doctor Settings", roles: ["admin", "doctor"] },
  { href: "/supplies", label: "Medical Supplies", roles: ["admin", "doctor", "receptionist"] },
  { href: "/calendar", label: "Calendar", roles: ["admin", "doctor", "receptionist"] }
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [moreOpen, setMoreOpen] = useState(false);

  useEffect(() => {
    let active = true;
    async function loadCurrentUser() {
      if (!getAccessToken()) {
        if (active) setUser(null);
        return;
      }
      try {
        const currentUser = await api.me();
        if (active && getAccessToken()) setUser(currentUser);
      } catch {
        if (active) setUser(null);
      }
    }
    loadCurrentUser();
    const unsubscribe = subscribeAuthChanges(loadCurrentUser);
    return () => {
      active = false;
      unsubscribe();
    };
  }, []);

  useEffect(() => {
    if (!user?.is_demo_account) return;
    let timer: number | undefined;
    const resetTimer = () => {
      if (timer !== undefined) window.clearTimeout(timer);
      timer = window.setTimeout(async () => {
        await resetDemoClinic();
        clearTokens();
        router.replace("/login");
      }, 30 * 60 * 1000);
    };
    const events = ["mousemove", "keydown", "click", "touchstart", "scroll"];
    events.forEach((eventName) => window.addEventListener(eventName, resetTimer, { passive: true }));
    resetTimer();
    return () => {
      if (timer !== undefined) window.clearTimeout(timer);
      events.forEach((eventName) => window.removeEventListener(eventName, resetTimer));
    };
  }, [router, user?.is_demo_account]);

  async function signOut() {
    if (user?.is_demo_account) {
      await resetDemoClinic();
    }
    clearTokens();
    router.replace("/login");
  }

  const role = user?.role ?? null;
  const filteredItems = navItems.filter((item) => (role ? item.roles.includes(role) : !["/consultations/new", "/operations", "/payment", "/settings"].includes(item.href)));
  const primaryItems = filteredItems.filter((item) => ["/dashboard", "/patients", "/queue", "/operations"].includes(item.href));
  const moreItems = filteredItems.filter((item) => !primaryItems.includes(item));
  const moreActive = moreItems.some((item) => pathname === item.href || pathname.startsWith(`${item.href}/`));

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-20 border-b border-clinic-line bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-3 sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:px-8">
          <div>
            <Link href="/dashboard" className="text-lg font-semibold text-clinic-ink">
              Clinic Console
            </Link>
            <p className="text-xs font-medium uppercase tracking-wide text-clinic-muted">Ophthalmology</p>
          </div>
          <nav className="flex flex-wrap items-center gap-2 pb-1 lg:justify-end lg:pb-0">
            {primaryItems.map((item) => {
              const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`min-h-11 whitespace-nowrap rounded px-4 py-2 text-sm font-semibold transition ${
                    active ? "bg-clinic-teal text-white" : "bg-clinic-wash text-clinic-ink hover:bg-clinic-mint"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
            {moreItems.length > 0 ? (
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setMoreOpen((open) => !open)}
                  className={`min-h-11 rounded px-4 py-2 text-sm font-semibold transition ${
                    moreActive ? "bg-clinic-teal text-white" : "bg-clinic-wash text-clinic-ink hover:bg-clinic-mint"
                  }`}
                >
                  More
                </button>
                {moreOpen ? (
                  <div className="absolute right-0 z-30 mt-2 w-56 rounded border border-clinic-line bg-white p-2 shadow-soft">
                    {moreItems.map((item) => {
                      const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
                      return (
                        <Link
                          key={item.href}
                          href={item.href}
                          onClick={() => setMoreOpen(false)}
                          className={`block rounded px-3 py-2 text-sm font-semibold ${
                            active ? "bg-clinic-teal text-white" : "text-clinic-ink hover:bg-clinic-wash"
                          }`}
                        >
                          {item.label}
                        </Link>
                      );
                    })}
                  </div>
                ) : null}
              </div>
            ) : null}
            <button
              type="button"
              onClick={signOut}
              className="min-h-11 rounded border border-clinic-line bg-white px-4 py-2 text-sm font-semibold text-clinic-ink hover:bg-clinic-wash"
            >
              {user?.is_demo_account ? "Exit Demo" : "Sign Out"}
            </button>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-5 sm:px-6 lg:px-8">
        {user?.is_demo_account ? (
          <section className="mb-5 rounded border border-clinic-line bg-white p-4 shadow-soft">
            <div className="mb-3 flex flex-wrap items-center gap-2">
              <span className="rounded-full bg-clinic-teal px-3 py-1 text-xs font-bold uppercase tracking-wide text-white">Demo Mode</span>
              <span className="text-sm font-semibold text-clinic-ink">Changes made here are temporary and will be reset automatically.</span>
            </div>
            <p className="text-sm font-semibold text-clinic-ink">Interested in this software?</p>
            <p className="mt-1 text-sm text-clinic-muted">This is a demonstration environment created for showcasing the application.</p>
            <p className="mt-1 text-sm text-clinic-muted">For enquiries, customization or purchase:</p>
            <a className="mt-2 inline-block font-semibold text-clinic-teal" href="mailto:aryankapale10@gmail.com">
              aryankapale10@gmail.com
            </a>
          </section>
        ) : null}
        {children}
      </main>
    </div>
  );
}
