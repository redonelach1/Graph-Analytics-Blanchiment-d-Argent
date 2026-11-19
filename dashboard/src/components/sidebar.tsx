"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  ShieldAlert,
  LayoutDashboard,
  Users,
  Activity,
  GitBranch,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/", label: "Executive Overview", icon: LayoutDashboard },
  { href: "/alerts", label: "Fraud Ring Alerts", icon: ShieldAlert, badge: "Live" },
  { href: "/accounts", label: "Account Centrality", icon: Users },
  { href: "/health", label: "Pipeline Telemetry", icon: Activity },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-60 border-r border-border bg-card flex flex-col justify-between shrink-0 h-screen sticky top-0 select-none">
      <div>
        {/* Brand Header */}
        <div className="p-5 border-b border-border/60 flex items-center space-x-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-zinc-800 border border-zinc-700">
            <GitBranch className="h-4 w-4 text-zinc-100" />
          </div>
          <div>
            <h1 className="text-xs font-semibold text-foreground tracking-tight">AML GraphShield</h1>
            <p className="text-[10px] text-muted-foreground font-mono">Real-time Cycle Engine</p>
          </div>
        </div>

        {/* Navigation items */}
        <nav className="p-3 space-y-1">
          <div className="px-2.5 pb-2 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
            Surveillance
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
                  "flex items-center justify-between rounded-md px-2.5 py-2 text-xs font-medium transition-colors",
                  isActive
                    ? "bg-zinc-800 text-white font-semibold"
                    : "text-muted-foreground hover:bg-zinc-900 hover:text-foreground"
                )}
              >
                <div className="flex items-center space-x-2.5">
                  <Icon className={cn("h-4 w-4", isActive ? "text-zinc-100" : "text-zinc-400")} />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span className="rounded px-1.5 py-0.2 text-[9px] font-mono font-semibold bg-red-950 text-red-300 border border-red-800/60">
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* System Status Footer */}
      <div className="p-3 m-3 rounded-md border border-border/80 bg-zinc-900/60 text-xs">
        <div className="flex items-center justify-between mb-1">
          <span className="text-muted-foreground text-[11px]">Stream Status</span>
          <span className="flex items-center gap-1.5 text-[11px] font-mono text-emerald-400 font-medium">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
            Healthy
          </span>
        </div>
        <div className="text-[10px] text-muted-foreground font-mono flex justify-between">
          <span>Watermark Lag</span>
          <span className="text-zinc-300">120s (Event Horizon)</span>
        </div>
      </div>
    </aside>
  );
}
