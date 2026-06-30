"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, clearTokens } from "@/lib/api";
import type { UserRole } from "@/lib/types";

const navItems = [
  { href: "/dashboard", label: "Dashboard", roles: ["admin", "doctor", "receptionist"] },
  { href: "/patients", label: "Patients", roles: ["admin", "doctor", "receptionist"] },
  { href: "/queue", label: "Queue", roles: ["admin", "doctor", "receptionist"] },
  { href: "/consultations/new", label: "New Consultation", roles: ["admin", "doctor"] },
  { href: "/operations", label: "Operations", roles: ["admin", "doctor", "receptionist"] },
  { href: "/payment", label: "Analytics & Finance", roles: ["admin", "doctor"] },
  { href: "/settings", label: "Doctor Settings", roles: ["admin", "doctor"] },
  { href: "/supplies", label: "Medical Supplies", roles: ["admin", "doctor", "receptionist"] },
  { href: "/calendar", label: "Calendar", roles: ["admin", "doctor", "receptionist"] }
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [role, setRole] = useState<UserRole | null>(null);
  const [moreOpen, setMoreOpen] = useState(false);

  useEffect(() => {
    let active = true;
    api.me()
      .then((user) => {
        if (active) setRole(user.role);
      })
      .catch(() => {
        if (active) setRole(null);
      });
    return () => {
      active = false;
    };
  }, []);

  function signOut() {
    clearTokens();
    router.replace("/login");
  }

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
              Sign Out
            </button>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-5 sm:px-6 lg:px-8">{children}</main>
    </div>
  );
}
