import React from "react";
import Link from "next/link";
import {
  ShieldAlert,
  ArrowUpRight,
  TrendingUp,
  AlertTriangle,
  Wallet,
  Users,
  Activity,
  ChevronRight,
  CheckCircle2
} from "lucide-react";
import { Header } from "@/components/header";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { getAlerts, getPipelineHealth } from "@/lib/data-service";
import { formatCurrency, formatDate } from "@/lib/utils";

export default async function DashboardPage() {
  const alerts = await getAlerts();
  const health = await getPipelineHealth();

  const totalFlaggedVolume = alerts.reduce((acc, a) => acc + (a.total_amount || 0), 0);
  const highRiskCount = alerts.filter((a) => a.risk_level === "HIGH").length;
  const mediumRiskCount = alerts.filter((a) => a.risk_level === "MEDIUM").length;
  const lowRiskCount = alerts.filter((a) => a.risk_level === "LOW").length;

  return (
    <div className="flex-1 pb-12">
      <Header
        title="Executive Fraud Intelligence Overview"
        description="Continuous monitoring of directed financial cycles across sliding windows"
      />

      <main className="p-8 space-y-8 max-w-7xl">
        {/* KPI Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="bg-slate-900/60 border-border/60 hover:border-blue-500/40 transition-all">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Active Cycle Alerts
              </CardTitle>
              <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400">
                <ShieldAlert className="h-4 w-4" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-foreground flex items-baseline gap-2">
                {alerts.length}
                <span className="text-xs font-medium text-emerald-400 flex items-center">
                  <ArrowUpRight className="h-3 w-3" /> Live
                </span>
              </div>
              <p className="text-[11px] text-muted-foreground mt-1">
                10-min sliding window | 30s slide
              </p>
            </CardContent>
          </Card>

          <Card className="bg-slate-900/60 border-border/60 hover:border-red-500/40 transition-all">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Flagged Volume
              </CardTitle>
              <div className="p-2 rounded-lg bg-red-500/10 text-red-400">
                <Wallet className="h-4 w-4" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-foreground">
                {formatCurrency(totalFlaggedVolume, "MAD")}
              </div>
              <p className="text-[11px] text-muted-foreground mt-1">
                Across detected triangular loops
              </p>
            </CardContent>
          </Card>

          <Card className="bg-slate-900/60 border-border/60 hover:border-amber-500/40 transition-all">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                High Risk Rings
              </CardTitle>
              <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400">
                <AlertTriangle className="h-4 w-4" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-foreground flex items-baseline gap-2">
                {highRiskCount}
                <span className="text-xs font-semibold text-red-400">
                  {Math.round((highRiskCount / Math.max(alerts.length, 1)) * 100)}% of total
                </span>
              </div>
              <p className="text-[11px] text-muted-foreground mt-1">
                ≥ 100,000 MAD & balanced ratio
              </p>
            </CardContent>
          </Card>

          <Card className="bg-slate-900/60 border-border/60 hover:border-emerald-500/40 transition-all">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Monitored Entities
              </CardTitle>
              <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
                <Users className="h-4 w-4" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-foreground">
                {health.tables.account_graph_metrics.toLocaleString()}
              </div>
              <p className="text-[11px] text-muted-foreground mt-1">
                Enriched with PageRank & clusters
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Middle Section: Severity Distribution + Quick Action */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Risk Level Breakdown Card */}
          <Card className="bg-slate-900/60 border-border/60 lg:col-span-1">
            <CardHeader>
              <CardTitle className="text-sm font-semibold">Severity Breakdown</CardTitle>
              <CardDescription className="text-xs">
                Classification by monetary magnitude & ratio tolerance
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* High Risk */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-medium">
                  <span className="text-red-400 flex items-center gap-1.5">
                    <span className="h-2 w-2 rounded-full bg-red-500" /> High Risk
                  </span>
                  <span className="text-foreground font-bold">{highRiskCount} alerts</span>
                </div>
                <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
                  <div
                    className="h-full bg-red-500 rounded-full"
                    style={{ width: `${(highRiskCount / Math.max(alerts.length, 1)) * 100}%` }}
                  />
                </div>
              </div>

              {/* Medium Risk */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-medium">
                  <span className="text-amber-400 flex items-center gap-1.5">
                    <span className="h-2 w-2 rounded-full bg-amber-500" /> Medium Risk
                  </span>
                  <span className="text-foreground font-bold">{mediumRiskCount} alerts</span>
                </div>
                <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
                  <div
                    className="h-full bg-amber-500 rounded-full"
                    style={{ width: `${(mediumRiskCount / Math.max(alerts.length, 1)) * 100}%` }}
                  />
                </div>
              </div>

              {/* Low Risk */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-medium">
                  <span className="text-blue-400 flex items-center gap-1.5">
                    <span className="h-2 w-2 rounded-full bg-blue-500" /> Low Risk
                  </span>
                  <span className="text-foreground font-bold">{lowRiskCount} alerts</span>
                </div>
                <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
                  <div
                    className="h-full bg-blue-500 rounded-full"
                    style={{ width: `${(lowRiskCount / Math.max(alerts.length, 1)) * 100}%` }}
                  />
                </div>
              </div>

              <div className="pt-4 border-t border-border/40 text-[11px] text-muted-foreground">
                Evaluated against: <strong>TEMPORAL_TRIANGLE (v1)</strong>
              </div>
            </CardContent>
          </Card>

          {/* Real-time Streamlit vs Next.js Pipeline Card */}
          <Card className="bg-slate-900/60 border-border/60 lg:col-span-2 flex flex-col justify-between">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-sm font-semibold">
                    Streaming Detection Architecture
                  </CardTitle>
                  <CardDescription className="text-xs">
                    Delta Lake Lakehouse + Spark GraphFrames Micro-batch Engine
                  </CardDescription>
                </div>
                <Badge variant="outline" className="border-blue-500/40 text-blue-400 text-xs">
                  Active
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-3 gap-3 text-center text-xs">
                <div className="p-3 rounded-lg bg-slate-950/80 border border-border/50">
                  <div className="text-muted-foreground text-[10px] uppercase font-bold">Ingestion Source</div>
                  <div className="text-foreground font-semibold mt-1">Kafka (3 Partitions)</div>
                  <div className="text-[11px] text-emerald-400 mt-0.5">Continuous</div>
                </div>
                <div className="p-3 rounded-lg bg-slate-950/80 border border-border/50">
                  <div className="text-muted-foreground text-[10px] uppercase font-bold">Graph Detection</div>
                  <div className="text-foreground font-semibold mt-1">GraphFrames Motif</div>
                  <div className="text-[11px] text-blue-400 mt-0.5">A → B → C → A</div>
                </div>
                <div className="p-3 rounded-lg bg-slate-950/80 border border-border/50">
                  <div className="text-muted-foreground text-[10px] uppercase font-bold">Alert Sink</div>
                  <div className="text-foreground font-semibold mt-1">Delta Lake + Kafka</div>
                  <div className="text-[11px] text-amber-400 mt-0.5">Partitioned `dt, risk`</div>
                </div>
              </div>

              <div className="flex items-center justify-between p-3 rounded-lg bg-blue-600/10 border border-blue-500/20 text-xs">
                <span className="text-muted-foreground">
                  Highest priority laundering cycle detected at <strong>{alerts[0]?.event_max}</strong>
                </span>
                <Link href={`/investigate/${alerts[0]?.alert_id}`}>
                  <Button size="sm" className="h-7 text-xs gap-1 bg-blue-600 hover:bg-blue-500">
                    Investigate <ChevronRight className="h-3.5 w-3.5" />
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Live Detected Alerts Feed */}
        <Card className="bg-slate-900/60 border-border/60">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-sm font-semibold">Recent Fraud Cycle Alerts</CardTitle>
              <CardDescription className="text-xs">
                Discovered in the latest micro-batches with verified evidence subgraphs
              </CardDescription>
            </div>
            <Link href="/alerts">
              <Button variant="outline" size="sm" className="h-8 text-xs border-border/80">
                View All Alerts
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {alerts.map((alert) => (
                <div
                  key={alert.alert_id}
                  className="flex flex-col sm:flex-row sm:items-center justify-between p-4 rounded-xl border border-border/40 bg-slate-950/60 hover:border-blue-500/40 hover:bg-slate-900/40 transition-all gap-4"
                >
                  <div className="flex items-start space-x-3.5">
                    <div
                      className={`p-2 rounded-lg mt-0.5 ${
                        alert.risk_level === "HIGH"
                          ? "bg-red-500/10 text-red-400 border border-red-500/20"
                          : alert.risk_level === "MEDIUM"
                          ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                          : "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                      }`}
                    >
                      <ShieldAlert className="h-4 w-4" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-sm text-foreground">
                          {alert.alert_id}
                        </span>
                        <Badge
                          variant={
                            alert.risk_level === "HIGH"
                              ? "destructive"
                              : alert.risk_level === "MEDIUM"
                              ? "warning"
                              : "default"
                          }
                        >
                          {alert.risk_level}
                        </Badge>
                      </div>
                      <div className="text-xs text-muted-foreground mt-1 flex flex-wrap gap-x-4 gap-y-1">
                        <span>Accounts: <strong className="text-slate-300">{alert.account_ids.join(" ➔ ")} ➔ {alert.account_ids[0]}</strong></span>
                        <span>Currency: <strong className="text-slate-300">{alert.currency}</strong></span>
                        <span>Detected: <strong>{formatDate(alert.first_detected_at)}</strong></span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-4 self-end sm:self-center">
                    <div className="text-right">
                      <div className="text-sm font-bold text-emerald-400">
                        {formatCurrency(alert.total_amount || 0, alert.currency)}
                      </div>
                      <div className="text-[10px] text-muted-foreground">Cycle Volume</div>
                    </div>
                    <Link href={`/investigate/${alert.alert_id}`}>
                      <Button size="sm" variant="outline" className="h-8 text-xs gap-1 border-border/80">
                        Investigate <ChevronRight className="h-3 w-3" />
                      </Button>
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}

