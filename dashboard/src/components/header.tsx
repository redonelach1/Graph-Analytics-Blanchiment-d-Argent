"use client";

import React from "react";
import { RefreshCw, Search, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";

export function Header({ title, description }: { title: string; description?: string }) {
  return (
    <header className="h-14 border-b border-border bg-card/60 backdrop-blur px-8 flex items-center justify-between sticky top-0 z-20">
      <div>
        <h2 className="text-sm font-semibold text-foreground tracking-tight">{title}</h2>
        {description && <p className="text-[11px] text-muted-foreground">{description}</p>}
      </div>

      <div className="flex items-center space-x-3">
        {/* Search */}
        <div className="relative w-64">
          <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search account, alert ID..."
            className="w-full rounded-md border border-border bg-zinc-900/80 pl-8 pr-3 py-1 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-zinc-500 font-mono"
          />
        </div>

        {/* Refresh button */}
        <Button
          variant="outline"
          size="sm"
          className="h-8 gap-1.5 text-xs border-border text-muted-foreground hover:text-foreground hover:bg-zinc-800"
          onClick={() => window.location.reload()}
        >
          <RefreshCw className="h-3 w-3" />
          <span>Sync</span>
        </Button>

        {/* Compliance Badge */}
        <div className="flex items-center gap-1.5 rounded-md border border-border bg-zinc-900/60 px-2.5 py-1 text-[11px] text-zinc-300 font-mono">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
          <span>FATF Rules Active</span>
        </div>
      </div>
    </header>
  );
}
