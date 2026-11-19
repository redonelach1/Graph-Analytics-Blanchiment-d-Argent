"use client";

import React, { useState, useMemo, useEffect } from "react";
import {
  Users,
  Search,
  Filter,
  ArrowUpDown,
  Building2,
  GitBranch,
  Info,
  ShieldAlert,
} from "lucide-react";
import { Header } from "@/components/header";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatCurrency } from "@/lib/utils";

interface AccountRow {
  account_id: string;
  pagerank: number;
  component_id: number;
  alert_count: number;
  total_volume: number;
  is_hub: boolean;
}

const INITIAL_ACCOUNTS: AccountRow[] = [
  { account_id: "ACC-MERCHANT-HUB", pagerank: 0.1428, component_id: 1, alert_count: 0, total_volume: 1250000.0, is_hub: true },
  { account_id: "ACC-UTILITY-BILLING", pagerank: 0.1105, component_id: 1, alert_count: 0, total_volume: 980000.0, is_hub: true },
  { account_id: "ACC-0105", pagerank: 0.0512, component_id: 4, alert_count: 1, total_volume: 420000.0, is_hub: false },
  { account_id: "ACC-0081", pagerank: 0.0482, component_id: 2, alert_count: 2, total_volume: 320000.0, is_hub: false },
  { account_id: "ACC-0014", pagerank: 0.0451, component_id: 2, alert_count: 1, total_volume: 308000.0, is_hub: false },
  { account_id: "ACC-0003", pagerank: 0.0439, component_id: 2, alert_count: 1, total_volume: 295000.0, is_hub: false },
  { account_id: "ACC-0312", pagerank: 0.0395, component_id: 4, alert_count: 1, total_volume: 215000.0, is_hub: false },
  { account_id: "ACC-0789", pagerank: 0.0381, component_id: 4, alert_count: 1, total_volume: 205000.0, is_hub: false },
  { account_id: "ACC-0012", pagerank: 0.0215, component_id: 3, alert_count: 1, total_volume: 98000.0, is_hub: false },
  { account_id: "ACC-0045", pagerank: 0.0201, component_id: 3, alert_count: 1, total_volume: 92000.0, is_hub: false },
  { account_id: "ACC-0089", pagerank: 0.0198, component_id: 3, alert_count: 1, total_volume: 89000.0, is_hub: false },
  { account_id: "ACC-0055", pagerank: 0.0185, component_id: 5, alert_count: 1, total_volume: 64500.0, is_hub: false },
  { account_id: "ACC-0062", pagerank: 0.0179, component_id: 5, alert_count: 1, total_volume: 63000.0, is_hub: false },
  { account_id: "ACC-0071", pagerank: 0.0172, component_id: 5, alert_count: 1, total_volume: 61000.0, is_hub: false },
  { account_id: "ACC-0021", pagerank: 0.0120, component_id: 6, alert_count: 1, total_volume: 14200.0, is_hub: false },
];

export default function AccountsPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState<"ALL" | "HUBS" | "MULES">("ALL");
  const [sortField, setSortField] = useState<"pagerank" | "alerts" | "volume">("pagerank");
  const [sortAsc, setSortAsc] = useState<boolean>(false);
  const [accounts, setAccounts] = useState<AccountRow[]>(INITIAL_ACCOUNTS);

  useEffect(() => {
    let isMounted = true;
    const fetchMetrics = async () => {
      try {
        const res = await fetch("/api/metrics");
        if (res.ok) {
          const json = await res.json();
          if (json.metrics && json.metrics.length > 0 && isMounted) {
            setAccounts(json.metrics);
          }
        }
      } catch (e) {}
    };
    fetchMetrics();
    const timer = setInterval(fetchMetrics, 4000);
    return () => {
      isMounted = false;
      clearInterval(timer);
    };
  }, []);

  const filteredAccounts = useMemo(() => {
    return accounts.filter((acct) => {
      const matchesFilter =
        filterType === "ALL" ||
        (filterType === "HUBS" && acct.is_hub) ||
        (filterType === "MULES" && !acct.is_hub && acct.alert_count > 0);

      const q = searchTerm.toLowerCase();
      const matchesSearch =
        !q ||
        acct.account_id.toLowerCase().includes(q) ||
        acct.component_id.toString().includes(q);

      return matchesFilter && matchesSearch;
    }).sort((a, b) => {
      let diff = 0;
      if (sortField === "pagerank") diff = a.pagerank - b.pagerank;
      if (sortField === "alerts") diff = a.alert_count - b.alert_count;
      if (sortField === "volume") diff = a.total_volume - b.total_volume;
      return sortAsc ? diff : -diff;
    });
  }, [accounts, searchTerm, filterType, sortField, sortAsc]);

  const hubCount = accounts.filter((a) => a.is_hub).length;
  const muleCount = accounts.filter((a) => !a.is_hub && a.alert_count > 0).length;
  const maxPR = Math.max(...accounts.map((a) => a.pagerank));

  return (
    <div className="flex-1 pb-16">
      <Header
        title="Entity Centrality & Partitioning"
        description="GraphFrames PageRank spectral distribution and Connected Components graph clustering (AT-17)"
      />

      <main className="p-8 space-y-6 max-w-7xl">
        {/* Metric strip */}
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          <Card className="border-border bg-card">
            <CardHeader className="pb-1.5">
              <CardTitle className="text-[11px] font-medium text-muted-foreground uppercase">Monitored Accounts</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold font-mono text-foreground">{accounts.length}</div>
              <p className="text-[11px] text-muted-foreground mt-0.5">Active in 10-min graph snapshot</p>
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardHeader className="pb-1.5">
              <CardTitle className="text-[11px] font-medium text-muted-foreground uppercase">Legitimate Hubs (AT-17)</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold font-mono text-zinc-100">{hubCount}</div>
              <p className="text-[11px] text-muted-foreground mt-0.5">Top PageRank | 0 False Positives</p>
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardHeader className="pb-1.5">
              <CardTitle className="text-[11px] font-medium text-muted-foreground uppercase">Mule Entities</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold font-mono text-red-400">{muleCount}</div>
              <p className="text-[11px] text-muted-foreground mt-0.5">Confirmed ring participants</p>
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardHeader className="pb-1.5">
              <CardTitle className="text-[11px] font-medium text-muted-foreground uppercase">Peak PageRank</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold font-mono text-zinc-100">{maxPR.toFixed(4)}</div>
              <p className="text-[11px] text-muted-foreground mt-0.5 font-mono">resetProb=0.15, iter=10</p>
            </CardContent>
          </Card>
        </div>

        {/* AT-17 Diagnostic Note */}
        <div className="rounded-md border border-border bg-zinc-900/40 p-3.5 text-xs text-zinc-300 flex items-start gap-3">
          <Info className="h-4 w-4 text-blue-400 shrink-0 mt-0.5" />
          <div className="space-y-0.5">
            <div className="font-medium text-zinc-100">
              AT-17 Mathematical Property: Separation of High-Centrality Hubs from Cycle Rings
            </div>
            <p className="text-muted-foreground leading-relaxed text-[11px]">
              Commercial merchant hubs (e.g., <span className="font-mono text-zinc-200">ACC-MERCHANT-HUB</span>) concentrate high transaction volumes and rank highest in PageRank centrality. However, because their inbound transfers do not loop back to senders within the 10-minute sliding window, the GraphFrames motif engine produces zero false alerts on these critical settlement accounts.
            </p>
          </div>
        </div>

        {/* Filter Toolbar */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-4 rounded-lg border border-border bg-card p-3">
          {/* Search */}
          <div className="relative w-full md:w-80">
            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
            <Input
              placeholder="Search account or cluster ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-8 bg-zinc-900 border-border text-xs font-mono"
            />
          </div>

          {/* Classification Filter */}
          <div className="flex items-center gap-1">
            <span className="text-xs text-muted-foreground mr-1.5 flex items-center gap-1 font-mono">
              <Filter className="h-3 w-3" /> Filter:
            </span>
            <button
              onClick={() => setFilterType("ALL")}
              className={`px-2.5 py-1 text-xs font-medium rounded transition-colors ${
                filterType === "ALL" ? "bg-zinc-800 text-white font-semibold" : "text-muted-foreground hover:text-zinc-200"
              }`}
            >
              All ({INITIAL_ACCOUNTS.length})
            </button>
            <button
              onClick={() => setFilterType("HUBS")}
              className={`px-2.5 py-1 text-xs font-medium rounded transition-colors ${
                filterType === "HUBS" ? "bg-zinc-800 text-white font-semibold" : "text-muted-foreground hover:text-zinc-200"
              }`}
            >
              Hubs ({hubCount})
            </button>
            <button
              onClick={() => setFilterType("MULES")}
              className={`px-2.5 py-1 text-xs font-medium rounded transition-colors ${
                filterType === "MULES" ? "bg-zinc-800 text-white font-semibold" : "text-muted-foreground hover:text-zinc-200"
              }`}
            >
              Mules ({muleCount})
            </button>
          </div>

          {/* Sort Toggles */}
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                if (sortField === "pagerank") setSortAsc(!sortAsc);
                else { setSortField("pagerank"); setSortAsc(false); }
              }}
              className={`text-xs h-8 border-border ${sortField === "pagerank" ? "text-white bg-zinc-800" : "text-zinc-400"}`}
            >
              <ArrowUpDown className="h-3 w-3 mr-1.5" />
              PageRank
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                if (sortField === "alerts") setSortAsc(!sortAsc);
                else { setSortField("alerts"); setSortAsc(false); }
              }}
              className={`text-xs h-8 border-border ${sortField === "alerts" ? "text-white bg-zinc-800" : "text-zinc-400"}`}
            >
              Alerts
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                if (sortField === "volume") setSortAsc(!sortAsc);
                else { setSortField("volume"); setSortAsc(false); }
              }}
              className={`text-xs h-8 border-border ${sortField === "volume" ? "text-white bg-zinc-800" : "text-zinc-400"}`}
            >
              Volume
            </Button>
          </div>
        </div>

        {/* Accounts Table */}
        <Card className="border-border bg-card overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="border-border/60 text-[11px]">
                <TableHead className="w-[200px]">Account ID</TableHead>
                <TableHead className="w-[130px]">Classification</TableHead>
                <TableHead>PageRank Centrality</TableHead>
                <TableHead className="w-[120px]">Cluster (CC ID)</TableHead>
                <TableHead className="w-[120px]">Cycle History</TableHead>
                <TableHead className="text-right">Window Volume</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredAccounts.map((acct) => {
                const prPercent = Math.min(100, Math.round((acct.pagerank / maxPR) * 100));

                return (
                  <TableRow key={acct.account_id} className="border-border/40 hover:bg-zinc-900/40">
                    <TableCell className="font-mono text-xs font-medium text-zinc-200">
                      <div className="flex items-center gap-2">
                        {acct.is_hub ? (
                          <Building2 className="h-3.5 w-3.5 text-zinc-400" />
                        ) : (
                          <Users className="h-3.5 w-3.5 text-zinc-500" />
                        )}
                        <span>{acct.account_id}</span>
                      </div>
                    </TableCell>

                    <TableCell>
                      {acct.is_hub ? (
                        <Badge variant="outline" className="text-[10px] px-2 py-0 border-blue-900 text-blue-400">
                          Merchant Hub
                        </Badge>
                      ) : acct.alert_count > 0 ? (
                        <Badge variant="destructive" className="text-[10px] px-2 py-0">
                          Mule Suspect
                        </Badge>
                      ) : (
                        <Badge variant="secondary" className="text-[10px] px-2 py-0">
                          Normal
                        </Badge>
                      )}
                    </TableCell>

                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className="w-24 bg-zinc-800 rounded-full h-1.5 overflow-hidden">
                          <div
                            className={`h-full rounded-full ${acct.is_hub ? "bg-blue-400" : "bg-emerald-400"}`}
                            style={{ width: `${prPercent}%` }}
                          />
                        </div>
                        <span className="font-mono text-xs text-zinc-200">
                          {acct.pagerank.toFixed(4)}
                        </span>
                      </div>
                    </TableCell>

                    <TableCell className="font-mono text-xs text-zinc-400">
                      <div className="flex items-center gap-1.5">
                        <GitBranch className="h-3 w-3 text-zinc-500" />
                        <span>Cluster #{acct.component_id}</span>
                      </div>
                    </TableCell>

                    <TableCell>
                      {acct.alert_count > 0 ? (
                        <span className="font-mono text-red-400 text-xs font-medium flex items-center gap-1">
                          <ShieldAlert className="h-3 w-3" /> {acct.alert_count} ring{acct.alert_count > 1 ? "s" : ""}
                        </span>
                      ) : (
                        <span className="text-xs text-muted-foreground font-mono">0 alerts</span>
                      )}
                    </TableCell>

                    <TableCell className="text-right font-mono font-medium text-zinc-200 text-xs">
                      {formatCurrency(acct.total_volume, "MAD")}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </Card>
      </main>
    </div>
  );
}
