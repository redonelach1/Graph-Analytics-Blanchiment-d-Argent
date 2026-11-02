"use client";

import React, { useState, useMemo } from "react";
import Link from "next/link";
import {
  ShieldAlert,
  Search,
  SlidersHorizontal,
  ChevronRight,
  ExternalLink,
  AlertTriangle,
  ArrowUpDown,
  Filter,
  CheckCircle2,
  Calendar,
  Layers
} from "lucide-react";
import { Header } from "@/components/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
import { formatCurrency, formatDate } from "@/lib/utils";

// Mock data imported on client
const INITIAL_ALERTS = [
  {
    alert_id: "ALT-7D29F4C1B039A8E2",
    cycle_id: "CYC-9B14E2F3A8C7",
    rule_id: "TEMPORAL_TRIANGLE",
    risk_level: "HIGH",
    reason_codes: ["DIRECTED_TRIANGLE", "SAME_CURRENCY", "HIGH_VALUE_THRESHOLD_MET", "AMOUNT_RATIO_TOLERANT_1.08"],
    account_ids: ["ACC-0081", "ACC-0014", "ACC-0003"],
    transaction_ids: ["TXN-64CAB8C7BF32", "TXN-E7D6A14A8A5F", "TXN-B55D9821222B"],
    currency: "MAD",
    first_detected_at: "2026-11-02 19:08:16",
    event_min: "2026-11-02 19:08:15",
    event_max: "2026-11-02 19:12:34",
    total_amount: 463859.44,
  },
  {
    alert_id: "ALT-5B81C40D9E12FA47",
    cycle_id: "CYC-AML-20K-042",
    rule_id: "TEMPORAL_TRIANGLE",
    risk_level: "HIGH",
    reason_codes: ["DIRECTED_TRIANGLE", "SAME_CURRENCY", "HIGH_VALUE_THRESHOLD_MET", "RAPID_DISPERSAL"],
    account_ids: ["ACC-0105", "ACC-0312", "ACC-0789"],
    transaction_ids: ["TXN-AML-0042A", "TXN-AML-0042B", "TXN-AML-0042C"],
    currency: "MAD",
    first_detected_at: "2026-11-02 16:30:15",
    event_min: "2026-11-02 16:26:00",
    event_max: "2026-11-02 16:29:45",
    total_amount: 620000.00,
  },
  {
    alert_id: "ALT-3C89B102A4E7F912",
    cycle_id: "CYC-4A29E8D102C3",
    rule_id: "TEMPORAL_TRIANGLE",
    risk_level: "MEDIUM",
    reason_codes: ["DIRECTED_TRIANGLE", "SAME_CURRENCY", "MEDIUM_VALUE_THRESHOLD_MET"],
    account_ids: ["ACC-0012", "ACC-0045", "ACC-0089"],
    transaction_ids: ["TXN-1A2B3C4D5E6F", "TXN-7G8H9I0J1K2L", "TXN-3M4N5O6P7Q8R"],
    currency: "MAD",
    first_detected_at: "2026-11-02 18:45:22",
    event_min: "2026-11-02 18:41:00",
    event_max: "2026-11-02 18:44:30",
    total_amount: 87400.00,
  },
  {
    alert_id: "ALT-9D44F2A1E8B07C33",
    cycle_id: "CYC-AML-20K-118",
    rule_id: "TEMPORAL_TRIANGLE",
    risk_level: "MEDIUM",
    reason_codes: ["DIRECTED_TRIANGLE", "SAME_CURRENCY", "MEDIUM_VALUE_THRESHOLD_MET"],
    account_ids: ["ACC-0055", "ACC-0062", "ACC-0071"],
    transaction_ids: ["TXN-AML-0118A", "TXN-AML-0118B", "TXN-AML-0118C"],
    currency: "MAD",
    first_detected_at: "2026-11-02 15:10:00",
    event_min: "2026-11-02 15:05:30",
    event_max: "2026-11-02 15:09:12",
    total_amount: 95000.00,
  },
  {
    alert_id: "ALT-E1A7D0924C58B331",
    cycle_id: "CYC-1F08C23A9E71",
    rule_id: "TEMPORAL_TRIANGLE",
    risk_level: "LOW",
    reason_codes: ["DIRECTED_TRIANGLE", "SAME_CURRENCY", "LOW_VALUE_CYCLE"],
    account_ids: ["ACC-0021", "ACC-0067", "ACC-0034"],
    transaction_ids: ["TXN-9A8B7C6D5E4F", "TXN-3G2H1I0J9K8L", "TXN-5M6N7O8P9Q0R"],
    currency: "MAD",
    first_detected_at: "2026-11-02 17:12:05",
    event_min: "2026-11-02 17:08:10",
    event_max: "2026-11-02 17:11:40",
    total_amount: 14200.00,
  }
];

export default function AlertsPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedRisk, setSelectedRisk] = useState<string>("ALL");
  const [sortField, setSortField] = useState<"time" | "amount">("time");
  const [sortAsc, setSortAsc] = useState<boolean>(false);

  const filteredAlerts = useMemo(() => {
    return INITIAL_ALERTS.filter((alert) => {
      const matchesRisk = selectedRisk === "ALL" || alert.risk_level === selectedRisk;
      const q = searchTerm.toLowerCase();
      const matchesSearch =
        !q ||
        alert.alert_id.toLowerCase().includes(q) ||
        alert.cycle_id.toLowerCase().includes(q) ||
        alert.account_ids.some((acc) => acc.toLowerCase().includes(q)) ||
        alert.reason_codes.some((r) => r.toLowerCase().includes(q));

      return matchesRisk && matchesSearch;
    }).sort((a, b) => {
      if (sortField === "amount") {
        return sortAsc
          ? (a.total_amount || 0) - (b.total_amount || 0)
          : (b.total_amount || 0) - (a.total_amount || 0);
      } else {
        return sortAsc
          ? new Date(a.first_detected_at).getTime() - new Date(b.first_detected_at).getTime()
          : new Date(b.first_detected_at).getTime() - new Date(a.first_detected_at).getTime();
      }
    });
  }, [searchTerm, selectedRisk, sortField, sortAsc]);

  const totalFilteredVolume = filteredAlerts.reduce((sum, a) => sum + (a.total_amount || 0), 0);
  const highCount = INITIAL_ALERTS.filter((a) => a.risk_level === "HIGH").length;
  const mediumCount = INITIAL_ALERTS.filter((a) => a.risk_level === "MEDIUM").length;
  const lowCount = INITIAL_ALERTS.filter((a) => a.risk_level === "LOW").length;

  return (
    <div className="flex-1 pb-16">
      <Header
        title="Fraud Alerts & Ring Inquiries"
        description="Deterministic temporal cycle alerts published to Delta Lake & Kafka fraud-alerts"
      />

      <main className="p-8 space-y-6 max-w-7xl">
        {/* KPI Summary strip */}
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          <Card className="bg-slate-900/60 border-border/60">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-semibold text-muted-foreground uppercase">Total Alerts</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-foreground">{INITIAL_ALERTS.length}</div>
              <p className="text-[11px] text-muted-foreground mt-0.5">Deduplicated by canonical hash</p>
            </CardContent>
          </Card>

          <Card className="bg-slate-900/60 border-border/60">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-semibold text-muted-foreground uppercase">High Risk Rings</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-400">{highCount}</div>
              <p className="text-[11px] text-muted-foreground mt-0.5">Volume ≥ 100,000 MAD</p>
            </CardContent>
          </Card>

          <Card className="bg-slate-900/60 border-border/60">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-semibold text-muted-foreground uppercase">Medium Risk</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-amber-400">{mediumCount}</div>
              <p className="text-[11px] text-muted-foreground mt-0.5">Volume 20k - 100k MAD</p>
            </CardContent>
          </Card>

          <Card className="bg-slate-900/60 border-border/60">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-semibold text-muted-foreground uppercase">Filtered Volume</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-emerald-400">
                {formatCurrency(totalFilteredVolume, "MAD")}
              </div>
              <p className="text-[11px] text-muted-foreground mt-0.5">{filteredAlerts.length} cycles active</p>
            </CardContent>
          </Card>
        </div>

        {/* Filter Toolbar */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-4 rounded-xl border border-border/70 bg-slate-900/70 p-4 backdrop-blur-md">
          {/* Search Input */}
          <div className="relative w-full md:w-96">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search Alert ID, Account ID, or Cycle ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 bg-slate-950/80 border-border/80 text-xs"
            />
          </div>

          {/* Risk Level Pills */}
          <div className="flex items-center gap-1.5 w-full md:w-auto overflow-x-auto pb-1 md:pb-0">
            <span className="text-xs text-muted-foreground mr-1 flex items-center gap-1">
              <Filter className="h-3.5 w-3.5" /> Risk:
            </span>
            {["ALL", "HIGH", "MEDIUM", "LOW"].map((level) => {
              const isActive = selectedRisk === level;
              return (
                <button
                  key={level}
                  onClick={() => setSelectedRisk(level)}
                  className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all ${
                    isActive
                      ? level === "HIGH"
                        ? "bg-red-500/20 text-red-300 border border-red-500/40"
                        : level === "MEDIUM"
                        ? "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                        : level === "LOW"
                        ? "bg-blue-500/20 text-blue-300 border border-blue-500/40"
                        : "bg-slate-700 text-white border border-slate-600"
                      : "text-muted-foreground hover:bg-slate-800/80 border border-transparent"
                  }`}
                >
                  {level}
                </button>
              );
            })}
          </div>

          {/* Sorting controls */}
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                if (sortField === "amount") {
                  setSortAsc(!sortAsc);
                } else {
                  setSortField("amount");
                  setSortAsc(false);
                }
              }}
              className={`text-xs h-8 ${sortField === "amount" ? "border-primary text-primary" : ""}`}
            >
              <ArrowUpDown className="h-3.5 w-3.5 mr-1" />
              Volume
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                if (sortField === "time") {
                  setSortAsc(!sortAsc);
                } else {
                  setSortField("time");
                  setSortAsc(false);
                }
              }}
              className={`text-xs h-8 ${sortField === "time" ? "border-primary text-primary" : ""}`}
            >
              <Calendar className="h-3.5 w-3.5 mr-1" />
              Timestamp
            </Button>
          </div>
        </div>

        {/* Alerts Table */}
        <Card className="bg-slate-900/60 border-border/60 overflow-hidden">
          <Table>
            <TableHeader className="bg-slate-950/80">
              <TableRow className="border-border/60 hover:bg-transparent">
                <TableHead className="w-[180px] text-xs font-semibold">Alert & Cycle ID</TableHead>
                <TableHead className="w-[100px] text-xs font-semibold">Risk Level</TableHead>
                <TableHead className="text-xs font-semibold">Target Accounts (Cycle Loop)</TableHead>
                <TableHead className="text-xs font-semibold text-right">Flagged Volume</TableHead>
                <TableHead className="text-xs font-semibold">Event Window</TableHead>
                <TableHead className="text-xs font-semibold">Reason Codes</TableHead>
                <TableHead className="w-[140px] text-xs font-semibold text-right">Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredAlerts.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="h-32 text-center text-muted-foreground">
                    No fraud alerts match the search criteria or risk filter.
                  </TableCell>
                </TableRow>
              ) : (
                filteredAlerts.map((alert) => (
                  <TableRow
                    key={alert.alert_id}
                    className="border-border/40 hover:bg-slate-800/40 transition-colors group"
                  >
                    <TableCell className="font-mono text-xs">
                      <div className="font-semibold text-foreground">{alert.alert_id}</div>
                      <div className="text-[11px] text-muted-foreground flex items-center gap-1 mt-0.5">
                        <Layers className="h-3 w-3" /> {alert.cycle_id}
                      </div>
                    </TableCell>

                    <TableCell>
                      <Badge
                        variant={
                          alert.risk_level === "HIGH"
                            ? "destructive"
                            : alert.risk_level === "MEDIUM"
                            ? "warning"
                            : "outline"
                        }
                      >
                        {alert.risk_level}
                      </Badge>
                    </TableCell>

                    <TableCell>
                      <div className="flex items-center gap-1.5 flex-wrap">
                        {alert.account_ids.map((acct, idx) => (
                          <React.Fragment key={acct}>
                            <span className="font-mono text-[11px] bg-slate-950 px-2 py-0.5 rounded border border-border/60 text-slate-300">
                              {acct}
                            </span>
                            {idx < alert.account_ids.length - 1 && (
                              <span className="text-muted-foreground text-xs">→</span>
                            )}
                          </React.Fragment>
                        ))}
                      </div>
                    </TableCell>

                    <TableCell className="text-right">
                      <span className="font-bold text-emerald-400 font-mono text-sm">
                        {formatCurrency(alert.total_amount || 0, alert.currency)}
                      </span>
                    </TableCell>

                    <TableCell className="text-xs text-muted-foreground">
                      <div className="text-[11px] text-slate-300 font-medium">
                        {formatDate(alert.first_detected_at)}
                      </div>
                      <div className="text-[10px] text-muted-foreground">
                        Span: {formatDate(alert.event_min).split(" ")[1]} - {formatDate(alert.event_max).split(" ")[1]}
                      </div>
                    </TableCell>

                    <TableCell>
                      <div className="flex flex-wrap gap-1 max-w-[220px]">
                        {alert.reason_codes.slice(0, 2).map((code) => (
                          <span
                            key={code}
                            className="text-[9px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700/60"
                          >
                            {code}
                          </span>
                        ))}
                        {alert.reason_codes.length > 2 && (
                          <span className="text-[9px] text-muted-foreground px-1">
                            +{alert.reason_codes.length - 2} more
                          </span>
                        )}
                      </div>
                    </TableCell>

                    <TableCell className="text-right">
                      <Link href={`/investigate/${alert.alert_id}`}>
                        <Button
                          size="sm"
                          className="h-8 text-xs bg-blue-600 hover:bg-blue-500 text-white shadow-sm shadow-blue-500/20 group-hover:scale-105 transition-all"
                        >
                          Investigate
                          <ChevronRight className="h-3.5 w-3.5 ml-1" />
                        </Button>
                      </Link>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </Card>
      </main>
    </div>
  );
}

