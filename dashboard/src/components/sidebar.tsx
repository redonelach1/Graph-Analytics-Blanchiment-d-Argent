"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  ShieldAlert,
  LayoutDashboard,
  Network,
  Users,
  Activity,
  Layers,
  ChevronRight
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/", label: "Overview", icon: LayoutDashboard },
  { href: "/alerts", label: "Fraud Alerts", icon: ShieldAlert, badge: "Live" },
  { href: "/accounts", label: "Account Centrality", icon: Users },
  { href: "/health", label: "Pipeline Telemetry", icon: Activity },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 border-r border-border/60 bg-slate-950/70 backdrop-blur-xl flex flex-col justify-between shrink-0 h-screen sticky top-0">
      <div>
        {/* Brand Header */}
        <div className="p-6 border-b border-border/40 flex items-center space-x-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 shadow-lg shadow-blue-500/20">
            <Network className="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-foreground tracking-tight">AML GraphShield</h1>
            <p className="text-[11px] text-muted-foreground font-medium">Real-time Cycle Detector</p>
          </div>
        </div>

        {/* Navigation items */}
        <nav className="p-4 space-y-1.5">
          <div className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground/70">
            Analytics & Investigation
          </div>
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive =
              item.href === "/"
                ? pathname === "/"
                : pathname.startsWith(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center justify-between rounded-lg px-3 py-2.5 text-sm font-medium transition-all group",
                  isActive
                    ? "bg-blue-600/15 text-blue-400 border border-blue-500/30 shadow-sm"
                    : "text-muted-foreground hover:bg-muted/50 hover:text-foreground"
                )}
              >
                <div className="flex items-center space-x-3">
                  <Icon className={cn("h-4 w-4", isActive ? "text-blue-400" : "text-muted-foreground group-hover:text-foreground")} />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span className="rounded-full bg-red-500/20 px-2 py-0.5 text-[10px] font-semibold text-red-400 border border-red-500/30">
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* System Status Footer */}
      <div className="p-4 m-4 rounded-xl border border-border/50 bg-slate-900/60 text-xs">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-muted-foreground font-medium">Engine Mode</span>
          <span className="flex items-center gap-1.5 font-semibold text-emerald-400">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
            Online
          </span>
        </div>
        <div className="text-[11px] text-muted-foreground flex justify-between">
          <span>Watermark Latency</span>
          <span className="text-foreground font-medium">120s (MAD)</span>
        </div>
      </div>
    </aside>
  );
}

