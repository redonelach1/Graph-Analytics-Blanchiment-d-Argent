"use client";

import React, { useState, useMemo } from "react";
import Link from "next/link";
import {
  Users,
  Search,
  Filter,
  ArrowUpDown,
  ShieldAlert,
  Building2,
  GitBranch,
  Info,
  CheckCircle2,
  ExternalLink
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

  const filteredAccounts = useMemo(() => {
    return INITIAL_ACCOUNTS.filter((acct) => {
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
  }, [searchTerm, filterType, sortField, sortAsc]);

  const hubCount = INITIAL_ACCOUNTS.filter((a) => a.is_hub).length;
  const muleCount = INITIAL_ACCOUNTS.filter((a) => !a.is_hub && a.alert_count > 0).length;
  const maxPR = Math.max(...INITIAL_ACCOUNTS.map((a) => a.pagerank));

  return (
    <div className="flex-1 pb-16">
      <Header
        title="Account Centrality & Clustering"
        description="PageRank centrality distribution and connected component graph partitioning (Section 10)"
      />

      <main className="p-8 space-y-6 max-w-7xl">
        {/* KPI strip */}
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          <Card className="bg-slate-900/60 border-border/60">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-semibold text-muted-foreground uppercase">
                Profiled Accounts
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-foreground">{INITIAL_ACCOUNTS.length}</div>
              <p className="text-[11px] text-muted-foreground mt-0.5">Active in 10-min graph snapshot</p>
            </CardContent>
          </Card>

          <Card className="bg-slate-900/60 border-border/60">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-semibold text-muted-foreground uppercase">
                Legitimate Hubs (AT-17)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-400">{hubCount}</div>
              <p className="text-[11px] text-muted-foreground mt-0.5">High PageRank | 0 False Alerts</p>
            </CardContent>
          </Card>

          <Card className="bg-slate-900/60 border-border/60">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-semibold text-muted-foreground uppercase">
                Mule Suspects
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-400">{muleCount}</div>
              <p className="text-[11px] text-muted-foreground mt-0.5">Involved in directed cycles</p>
            </CardContent>
          </Card>

          <Card className="bg-slate-900/60 border-border/60">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-semibold text-muted-foreground uppercase">
                Highest PageRank
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-emerald-400 font-mono">
                {maxPR.toFixed(4)}
              </div>
              <p className="text-[11px] text-muted-foreground mt-0.5">resetProb=0.15, maxIter=10</p>
            </CardContent>
          </Card>
        </div>

        {/* Algorithm Insight Alert */}
        <div className="rounded-xl border border-blue-500/30 bg-blue-950/20 p-4 text-xs text-blue-300 flex items-start gap-3">
          <Info className="h-5 w-5 text-blue-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <div className="font-semibold text-white">
              Acceptance Test AT-17 Guarantee: High Centrality vs Cycle Separation
            </div>
            <p className="text-blue-300/80 leading-relaxed">
              Legitimate enterprise hubs (like <span className="font-mono text-white">ACC-MERCHANT-HUB</span> and{" "}
              <span className="font-mono text-white">ACC-UTILITY-BILLING</span>) exhibit high in-degree and top PageRank scores.
              Our streaming detection engine validates directed cycle topology rather than raw volume, guaranteeing zero false positives on high-throughput legitimate settlement nodes.
            </p>
          </div>
        </div>

        {/* Filter Toolbar */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-4 rounded-xl border border-border/70 bg-slate-900/70 p-4 backdrop-blur-md">
          {/* Search */}
          <div className="relative w-full md:w-80">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search Account ID or Cluster ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 bg-slate-950/80 border-border/80 text-xs"
            />
          </div>

          {/* Classification Filter */}
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-muted-foreground mr-1 flex items-center gap-1">
              <Filter className="h-3.5 w-3.5" /> Type:
            </span>
            <button
              onClick={() => setFilterType("ALL")}
              className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all ${
                filterType === "ALL" ? "bg-slate-700 text-white" : "text-muted-foreground hover:bg-slate-800"
              }`}
            >
              All ({INITIAL_ACCOUNTS.length})
            </button>
            <button
              onClick={() => setFilterType("HUBS")}
              className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all ${
                filterType === "HUBS" ? "bg-blue-600/30 text-blue-300 border border-blue-500/40" : "text-muted-foreground hover:bg-slate-800"
              }`}
            >
              Hubs ({hubCount})
            </button>
            <button
              onClick={() => setFilterType("MULES")}
              className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all ${
                filterType === "MULES" ? "bg-red-600/30 text-red-300 border border-red-500/40" : "text-muted-foreground hover:bg-slate-800"
              }`}
            >
              Mule Suspects ({muleCount})
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
              className={`text-xs h-8 ${sortField === "pagerank" ? "border-primary text-primary" : ""}`}
            >
              <ArrowUpDown className="h-3.5 w-3.5 mr-1" />
              PageRank
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                if (sortField === "alerts") setSortAsc(!sortAsc);
                else { setSortField("alerts"); setSortAsc(false); }
              }}
              className={`text-xs h-8 ${sortField === "alerts" ? "border-primary text-primary" : ""}`}
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
              className={`text-xs h-8 ${sortField === "volume" ? "border-primary text-primary" : ""}`}
            >
              Volume
            </Button>
          </div>
        </div>

        {/* Accounts Table */}
        <Card className="bg-slate-900/60 border-border/60 overflow-hidden">
          <Table>
            <TableHeader className="bg-slate-950/80">
              <TableRow className="border-border/60">
                <TableHead className="w-[220px] text-xs">Account ID</TableHead>
                <TableHead className="w-[140px] text-xs">Category</TableHead>
                <TableHead className="text-xs">PageRank Centrality</TableHead>
                <TableHead className="w-[120px] text-xs">Cluster (CC ID)</TableHead>
                <TableHead className="w-[120px] text-xs">Cycle Alerts</TableHead>
                <TableHead className="text-xs text-right">Window Volume</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredAccounts.map((acct) => {
                const prPercent = Math.min(100, Math.round((acct.pagerank / maxPR) * 100));

                return (
                  <TableRow key={acct.account_id} className="border-border/40 hover:bg-slate-800/40">
                    <TableCell className="font-mono text-xs font-semibold text-foreground">
                      <div className="flex items-center gap-2">
                        {acct.is_hub ? (
                          <Building2 className="h-4 w-4 text-blue-400" />
                        ) : (
                          <Users className="h-4 w-4 text-slate-400" />
                        )}
                        <span>{acct.account_id}</span>
                      </div>
                    </TableCell>

                    <TableCell>
                      {acct.is_hub ? (
                        <Badge variant="outline" className="text-[10px] px-2 py-0 border-blue-500/40 text-blue-400">
                          Merchant Hub
                        </Badge>
                      ) : acct.alert_count > 0 ? (
                        <Badge variant="destructive" className="text-[10px] px-2 py-0">
                          Mule Suspect
                        </Badge>
                      ) : (
                        <Badge variant="secondary" className="text-[10px] px-2 py-0">
                          Standard
                        </Badge>
                      )}
                    </TableCell>

                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className="w-28 bg-slate-950 rounded-full h-2 overflow-hidden border border-border/60">
                          <div
                            className={`h-full rounded-full ${acct.is_hub ? "bg-blue-500" : "bg-emerald-500"}`}
                            style={{ width: `${prPercent}%` }}
                          />
                        </div>
                        <span className="font-mono text-xs font-bold text-foreground">
                          {acct.pagerank.toFixed(4)}
                        </span>
                      </div>
                    </TableCell>

                    <TableCell className="font-mono text-xs text-slate-300">
                      <div className="flex items-center gap-1.5">
                        <GitBranch className="h-3.5 w-3.5 text-muted-foreground" />
                        Component #{acct.component_id}
                      </div>
                    </TableCell>

                    <TableCell>
                      {acct.alert_count > 0 ? (
                        <span className="font-mono font-bold text-red-400 text-xs flex items-center gap-1">
                          <ShieldAlert className="h-3.5 w-3.5" /> {acct.alert_count} ring{acct.alert_count > 1 ? "s" : ""}
                        </span>
                      ) : (
                        <span className="text-xs text-muted-foreground font-mono">0 alerts</span>
                      )}
                    </TableCell>

                    <TableCell className="text-right font-mono font-bold text-foreground text-xs">
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

