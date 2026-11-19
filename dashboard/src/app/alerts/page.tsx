"use client";

import React, { useState, useMemo, useEffect } from "react";
import Link from "next/link";
import {
  Search,
  ChevronRight,
  ArrowUpDown,
  Filter,
  Calendar,
  Layers,
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
import { FraudAlert } from "@/lib/data-service";

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
  },
];

export default function AlertsPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedRisk, setSelectedRisk] = useState<string>("ALL");
  const [sortField, setSortField] = useState<"time" | "amount">("time");
  const [sortAsc, setSortAsc] = useState<boolean>(false);
  const [alerts, setAlerts] = useState<any[]>(INITIAL_ALERTS);

  useEffect(() => {
    let isMounted = true;
    const fetchAlerts = async () => {
      try {
        const res = await fetch("/api/alerts");
        if (res.ok) {
          const json = await res.json();
          if (json.alerts && json.alerts.length > 0 && isMounted) {
            setAlerts(json.alerts);
          }
        }
      } catch (err) {}
    };
    fetchAlerts();
    const timer = setInterval(fetchAlerts, 4000);
    return () => {
      isMounted = false;
      clearInterval(timer);
    };
  }, []);

  const filteredAlerts = useMemo(() => {
    return alerts.filter((alert) => {
      const matchesRisk = selectedRisk === "ALL" || alert.risk_level === selectedRisk;
      const q = searchTerm.toLowerCase();
      const matchesSearch =
        !q ||
        alert.alert_id.toLowerCase().includes(q) ||
        alert.cycle_id.toLowerCase().includes(q) ||
        (alert.account_ids && alert.account_ids.some((acc: string) => acc.toLowerCase().includes(q))) ||
        (alert.reason_codes && alert.reason_codes.some((r: string) => r.toLowerCase().includes(q)));

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
  }, [alerts, searchTerm, selectedRisk, sortField, sortAsc]);

  const totalFilteredVolume = filteredAlerts.reduce((sum, a) => sum + (a.total_amount || 0), 0);
  const highCount = alerts.filter((a) => a.risk_level === "HIGH").length;
  const mediumCount = alerts.filter((a) => a.risk_level === "MEDIUM").length;

  return (
    <div className="flex-1 pb-16">
      <Header
        title="Fraud Alerts Ledger"
        description="Deterministic temporal cycle alerts published to Delta Lake & Kafka fraud-alerts"
      />

      <main className="p-8 space-y-6 max-w-7xl">
        {/* Metric strip */}
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          <Card className="border-border bg-card">
            <CardHeader className="pb-1.5">
              <CardTitle className="text-[11px] font-medium text-muted-foreground uppercase">Total Alerts</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold font-mono text-foreground">{INITIAL_ALERTS.length}</div>
              <p className="text-[11px] text-muted-foreground mt-0.5 font-mono">Deduplicated by SHA-256</p>
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardHeader className="pb-1.5">
              <CardTitle className="text-[11px] font-medium text-muted-foreground uppercase">High Risk</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold font-mono text-red-400">{highCount}</div>
              <p className="text-[11px] text-muted-foreground mt-0.5">Threshold ≥ 100,000 MAD</p>
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardHeader className="pb-1.5">
              <CardTitle className="text-[11px] font-medium text-muted-foreground uppercase">Medium Risk</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold font-mono text-amber-400">{mediumCount}</div>
              <p className="text-[11px] text-muted-foreground mt-0.5">Threshold 20k - 100k MAD</p>
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardHeader className="pb-1.5">
              <CardTitle className="text-[11px] font-medium text-muted-foreground uppercase">Selected Volume</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold font-mono text-zinc-100">
                {formatCurrency(totalFilteredVolume, "MAD")}
              </div>
              <p className="text-[11px] text-muted-foreground mt-0.5 font-mono">{filteredAlerts.length} cycles active</p>
            </CardContent>
          </Card>
        </div>

        {/* Filter Toolbar */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-4 rounded-lg border border-border bg-card p-3">
          {/* Search Input */}
          <div className="relative w-full md:w-80">
            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
            <Input
              placeholder="Search alert, cycle, or account ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-8 bg-zinc-900 border-border text-xs font-mono"
            />
          </div>

          {/* Risk Level Pills */}
          <div className="flex items-center gap-1">
            <span className="text-xs text-muted-foreground mr-1.5 flex items-center gap-1 font-mono">
              <Filter className="h-3 w-3" /> Tier:
            </span>
            {["ALL", "HIGH", "MEDIUM", "LOW"].map((level) => {
              const isActive = selectedRisk === level;
              return (
                <button
                  key={level}
                  onClick={() => setSelectedRisk(level)}
                  className={`px-2.5 py-1 text-xs font-medium rounded transition-colors ${
                    isActive
                      ? "bg-zinc-800 text-white font-semibold"
                      : "text-muted-foreground hover:text-zinc-200"
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
                if (sortField === "amount") setSortAsc(!sortAsc);
                else { setSortField("amount"); setSortAsc(false); }
              }}
              className={`text-xs h-8 border-border ${sortField === "amount" ? "text-white bg-zinc-800" : "text-zinc-400"}`}
            >
              <ArrowUpDown className="h-3 w-3 mr-1.5" />
              Volume
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                if (sortField === "time") setSortAsc(!sortAsc);
                else { setSortField("time"); setSortAsc(false); }
              }}
              className={`text-xs h-8 border-border ${sortField === "time" ? "text-white bg-zinc-800" : "text-zinc-400"}`}
            >
              <Calendar className="h-3 w-3 mr-1.5" />
              Timestamp
            </Button>
          </div>
        </div>

        {/* Alerts Table */}
        <Card className="border-border bg-card overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="border-border/60 text-[11px]">
                <TableHead className="w-[180px]">Alert / Cycle ID</TableHead>
                <TableHead className="w-[100px]">Risk Tier</TableHead>
                <TableHead>Entities Involved</TableHead>
                <TableHead className="text-right">Flagged Volume</TableHead>
                <TableHead>Event Window</TableHead>
                <TableHead>Reason Codes</TableHead>
                <TableHead className="w-[120px] text-right">Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredAlerts.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="h-28 text-center text-muted-foreground text-xs">
                    No fraud alerts match the search criteria.
                  </TableCell>
                </TableRow>
              ) : (
                filteredAlerts.map((alert) => (
                  <TableRow key={alert.alert_id} className="border-border/40 hover:bg-zinc-900/40">
                    <TableCell className="font-mono text-xs">
                      <div className="font-medium text-zinc-200">{alert.alert_id}</div>
                      <div className="text-[10px] text-muted-foreground flex items-center gap-1 mt-0.5">
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
                        className="text-[10px] px-2 py-0"
                      >
                        {alert.risk_level}
                      </Badge>
                    </TableCell>

                    <TableCell>
                      <div className="flex items-center gap-1 font-mono text-xs text-zinc-300 flex-wrap">
                        {alert.account_ids.map((acct: string, idx: number) => (
                          <React.Fragment key={acct}>
                            <span>{acct}</span>
                            {idx < alert.account_ids.length - 1 && (
                              <span className="text-zinc-600">→</span>
                            )}
                          </React.Fragment>
                        ))}
                      </div>
                    </TableCell>

                    <TableCell className="text-right font-mono font-medium text-zinc-200 text-xs">
                      {formatCurrency(alert.total_amount || 0, alert.currency)}
                    </TableCell>

                    <TableCell className="text-xs text-muted-foreground font-mono">
                      <div>{formatDate(alert.first_detected_at)}</div>
                      <div className="text-[10px] text-zinc-500">
                        {formatDate(alert.event_min).split(" ")[1]} - {formatDate(alert.event_max).split(" ")[1]}
                      </div>
                    </TableCell>

                    <TableCell>
                      <div className="flex flex-wrap gap-1 max-w-[200px]">
                        {alert.reason_codes.slice(0, 2).map((code: string) => (
                          <span
                            key={code}
                            className="text-[9px] px-1.5 py-0.5 rounded bg-zinc-900 text-zinc-400 border border-border font-mono"
                          >
                            {code}
                          </span>
                        ))}
                      </div>
                    </TableCell>

                    <TableCell className="text-right">
                      <Link href={`/investigate/${alert.alert_id}`}>
                        <Button
                          size="sm"
                          variant="outline"
                          className="h-7 text-xs border-border text-zinc-300 hover:text-white hover:bg-zinc-800"
                        >
                          Investigate
                          <ChevronRight className="h-3 w-3 ml-1" />
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
