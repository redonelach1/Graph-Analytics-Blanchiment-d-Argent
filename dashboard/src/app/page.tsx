import React from "react";
import Link from "next/link";
import {
  ShieldAlert,
  ArrowUpRight,
  AlertTriangle,
  Wallet,
  Users,
  ChevronRight,
  Database,
  Layers,
} from "lucide-react";
import { Header } from "@/components/header";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { getAlerts, getPipelineHealth } from "@/lib/data-service";
import { formatCurrency, formatDate } from "@/lib/utils";
import { AutoRefresh } from "@/components/auto-refresh";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export default async function DashboardPage() {
  const alerts = await getAlerts();
  const health = await getPipelineHealth();

  const totalFlaggedVolume = alerts.reduce((acc, a) => acc + (a.total_amount || 0), 0);
  const highRiskCount = alerts.filter((a) => a.risk_level === "HIGH").length;
  const mediumRiskCount = alerts.filter((a) => a.risk_level === "MEDIUM").length;
  const lowRiskCount = alerts.filter((a) => a.risk_level === "LOW").length;

  return (
    <div className="flex-1 pb-16">
      <AutoRefresh intervalMs={4000} />
      <Header
        title="Executive Fraud Intelligence"
        description="Continuous monitoring of circular layering rings across sliding transaction windows"
      />

      <main className="p-8 space-y-6 max-w-7xl">
        {/* KPI Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="border-border bg-card">
            <CardHeader className="flex flex-row items-center justify-between pb-1.5">
              <CardTitle className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
                Active Cycle Alerts
              </CardTitle>
              <ShieldAlert className="h-4 w-4 text-zinc-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold font-mono text-foreground flex items-baseline gap-2">
                {alerts.length}
                <span className="text-[11px] font-normal text-emerald-400 flex items-center font-sans">
                  <ArrowUpRight className="h-3 w-3 mr-0.5" /> Synchronized
                </span>
              </div>
              <p className="text-[11px] text-muted-foreground mt-1">
                10-min window | 30s slide cadence
              </p>
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardHeader className="flex flex-row items-center justify-between pb-1.5">
              <CardTitle className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
                Flagged Ring Volume
              </CardTitle>
              <Wallet className="h-4 w-4 text-zinc-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold font-mono text-zinc-100">
                {formatCurrency(totalFlaggedVolume, "MAD")}
              </div>
              <p className="text-[11px] text-muted-foreground mt-1">
                Across directed triangular loops
              </p>
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardHeader className="flex flex-row items-center justify-between pb-1.5">
              <CardTitle className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
                High Risk Rings
              </CardTitle>
              <AlertTriangle className="h-4 w-4 text-red-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold font-mono text-foreground flex items-baseline gap-2">
                {highRiskCount}
                <span className="text-xs font-mono text-red-400">
                  ({Math.round((highRiskCount / Math.max(alerts.length, 1)) * 100)}%)
                </span>
              </div>
              <p className="text-[11px] text-muted-foreground mt-1">
                Volume ≥ 100,000 MAD & ratio ≤ 1.15
              </p>
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardHeader className="flex flex-row items-center justify-between pb-1.5">
              <CardTitle className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
                Monitored Entities
              </CardTitle>
              <Users className="h-4 w-4 text-zinc-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold font-mono text-foreground">
                {health.tables.account_graph_metrics.toLocaleString()}
              </div>
              <p className="text-[11px] text-muted-foreground mt-1">
                Enriched with PageRank & clusters
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Middle Section: Severity Distribution + Architecture Status */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Risk Level Breakdown Card */}
          <Card className="border-border bg-card lg:col-span-1">
            <CardHeader className="pb-3">
              <CardTitle className="text-xs font-semibold text-foreground tracking-tight">
                Severity Distribution
              </CardTitle>
              <CardDescription className="text-[11px] text-muted-foreground">
                Classified by monetary value and transaction ratio tolerance
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3.5">
              {/* High Risk */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs">
                  <span className="text-red-400 font-medium flex items-center gap-1.5">
                    <span className="h-1.5 w-1.5 rounded-full bg-red-400" /> High Risk
                  </span>
                  <span className="font-mono text-zinc-200">{highRiskCount} alerts</span>
                </div>
                <div className="h-1.5 w-full rounded-full bg-zinc-800 overflow-hidden">
                  <div
                    className="h-full bg-red-500 rounded-full"
                    style={{ width: `${(highRiskCount / Math.max(alerts.length, 1)) * 100}%` }}
                  />
                </div>
              </div>

              {/* Medium Risk */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs">
                  <span className="text-amber-400 font-medium flex items-center gap-1.5">
                    <span className="h-1.5 w-1.5 rounded-full bg-amber-400" /> Medium Risk
                  </span>
                  <span className="font-mono text-zinc-200">{mediumRiskCount} alerts</span>
                </div>
                <div className="h-1.5 w-full rounded-full bg-zinc-800 overflow-hidden">
                  <div
                    className="h-full bg-amber-400 rounded-full"
                    style={{ width: `${(mediumRiskCount / Math.max(alerts.length, 1)) * 100}%` }}
                  />
                </div>
              </div>

              {/* Low Risk */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs">
                  <span className="text-zinc-400 font-medium flex items-center gap-1.5">
                    <span className="h-1.5 w-1.5 rounded-full bg-zinc-400" /> Low Risk
                  </span>
                  <span className="font-mono text-zinc-200">{lowRiskCount} alerts</span>
                </div>
                <div className="h-1.5 w-full rounded-full bg-zinc-800 overflow-hidden">
                  <div
                    className="h-full bg-zinc-500 rounded-full"
                    style={{ width: `${(lowRiskCount / Math.max(alerts.length, 1)) * 100}%` }}
                  />
                </div>
              </div>

              <div className="pt-3 border-t border-border/60 text-[11px] text-muted-foreground font-mono">
                Evaluated against: TEMPORAL_TRIANGLE (v1)
              </div>
            </CardContent>
          </Card>

          {/* Engine Status & Quick Navigation */}
          <Card className="border-border bg-card lg:col-span-2 flex flex-col justify-between">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-xs font-semibold text-foreground tracking-tight">
                    Streaming Engine & Storage Topology
                  </CardTitle>
                  <CardDescription className="text-[11px] text-muted-foreground">
                    Apache Spark 3.5.0 Structured Streaming + Delta Lake Lakehouse
                  </CardDescription>
                </div>
                <span className="text-[11px] font-mono font-medium text-emerald-400 flex items-center gap-1.5 border border-emerald-900/60 bg-emerald-950/40 px-2 py-0.5 rounded">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                  ACID Synchronized
                </span>
              </div>
            </CardHeader>
            <CardContent className="space-y-3.5">
              <div className="grid grid-cols-3 gap-3 text-xs">
                <div className="p-3 rounded-md bg-zinc-900/60 border border-border">
                  <div className="text-muted-foreground text-[10px] font-mono uppercase font-semibold">Message Broker</div>
                  <div className="text-zinc-200 font-medium mt-1">Kafka KRaft</div>
                  <div className="text-[11px] text-zinc-400 mt-0.5 font-mono">3 Partitions</div>
                </div>
                <div className="p-3 rounded-md bg-zinc-900/60 border border-border">
                  <div className="text-muted-foreground text-[10px] font-mono uppercase font-semibold">Detection Core</div>
                  <div className="text-zinc-200 font-medium mt-1">GraphFrames Motif</div>
                  <div className="text-[11px] text-zinc-400 mt-0.5 font-mono">(a)-[e1]-&gt;(b)...</div>
                </div>
                <div className="p-3 rounded-md bg-zinc-900/60 border border-border">
                  <div className="text-muted-foreground text-[10px] font-mono uppercase font-semibold">Lakehouse Sinks</div>
                  <div className="text-zinc-200 font-medium mt-1">Delta Lake Tables</div>
                  <div className="text-[11px] text-zinc-400 mt-0.5 font-mono">10 Tables Active</div>
                </div>
              </div>

              <div className="flex items-center justify-between p-3 rounded-md bg-zinc-900/80 border border-border text-xs">
                <span className="text-zinc-400">
                  Highest priority alert: <span className="text-zinc-100 font-mono font-medium">{alerts[0]?.alert_id}</span> ({formatCurrency(alerts[0]?.total_amount || 0, "MAD")})
                </span>
                <Link href={`/investigate/${alerts[0]?.alert_id}`}>
                  <Button size="sm" className="h-7 text-xs gap-1 font-medium bg-zinc-100 text-zinc-900 hover:bg-white">
                    Investigate Dossier <ChevronRight className="h-3 w-3" />
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Live Detected Alerts Feed */}
        <Card className="border-border bg-card">
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <div>
              <CardTitle className="text-xs font-semibold text-foreground tracking-tight">
                Recent Directed Cycle Detections
              </CardTitle>
              <CardDescription className="text-[11px] text-muted-foreground">
                Verified financial cycles discovered in the active sliding window
              </CardDescription>
            </div>
            <Link href="/alerts">
              <Button variant="outline" size="sm" className="h-7 text-xs border-border text-zinc-300 hover:text-white">
                View All Alerts ({alerts.length})
              </Button>
            </Link>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow className="border-border/60 text-[11px]">
                  <TableHead className="w-[180px]">Alert ID</TableHead>
                  <TableHead className="w-[100px]">Risk Tier</TableHead>
                  <TableHead>Cycle Entities</TableHead>
                  <TableHead className="text-right">Flagged Volume</TableHead>
                  <TableHead>Window Timestamp</TableHead>
                  <TableHead className="w-[100px] text-right">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {alerts.slice(0, 4).map((alert) => (
                  <TableRow key={alert.alert_id} className="border-border/40 hover:bg-zinc-900/40">
                    <TableCell className="font-mono text-xs font-medium text-zinc-200">
                      {alert.alert_id}
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
                      <div className="flex items-center gap-1 font-mono text-xs text-zinc-300">
                        {alert.account_ids.map((acct, idx) => (
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
                      {formatDate(alert.first_detected_at)}
                    </TableCell>

                    <TableCell className="text-right">
                      <Link href={`/investigate/${alert.alert_id}`}>
                        <Button variant="ghost" size="sm" className="h-7 text-xs text-zinc-400 hover:text-white px-2">
                          Inspect <ChevronRight className="h-3.5 w-3.5 ml-0.5" />
                        </Button>
                      </Link>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
