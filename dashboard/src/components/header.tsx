"use client";

import React from "react";
import { Bell, RefreshCw, Search, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";

export function Header({ title, description }: { title: string; description?: string }) {
  return (
    <header className="h-16 border-b border-border/60 bg-slate-950/40 backdrop-blur-md px-8 flex items-center justify-between sticky top-0 z-30">
      <div>
        <h2 className="text-base font-semibold text-foreground tracking-tight">{title}</h2>
        {description && <p className="text-xs text-muted-foreground">{description}</p>}
      </div>

      <div className="flex items-center space-x-4">
        {/* Search */}
        <div className="relative w-64">
          <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search account, alert ID..."
            className="w-full rounded-lg border border-border/80 bg-slate-900/80 pl-9 pr-4 py-1.5 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
          />
        </div>

        {/* Refresh button */}
        <Button
          variant="outline"
          size="sm"
          className="h-8 gap-1.5 text-xs border-border/80 text-muted-foreground hover:text-foreground"
          onClick={() => window.location.reload()}
        >
          <RefreshCw className="h-3.5 w-3.5" />
          <span>Refresh</span>
        </Button>

        {/* Compliance Badge */}
        <div className="flex items-center gap-1.5 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1 text-xs text-emerald-400 font-medium">
          <ShieldCheck className="h-3.5 w-3.5" />
          <span>AML Rules Active</span>
        </div>
      </div>
    </header>
  );
}

