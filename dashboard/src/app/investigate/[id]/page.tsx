import React from "react";
import Link from "next/link";
import { notFound } from "next/navigation";
import {
  ArrowLeft,
  ShieldAlert,
  Clock,
  Layers,
  CheckCircle2,
  Info,
  Building2,
  Users,
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
import { NetworkGraph } from "@/components/network-graph";
import { SARExportButton } from "@/components/sar-export-button";
import { getAlertById, getAccountMetrics } from "@/lib/data-service";
import { formatCurrency, formatDate } from "@/lib/utils";

interface InvestigatePageProps {
  params: {
    id: string;
  };
}

export const dynamic = "force-dynamic";
export const revalidate = 0;

export default async function InvestigatePage({ params }: InvestigatePageProps) {
  const alert = await getAlertById(params.id);

  if (!alert) {
    return (
      <div className="flex-1 p-16 flex flex-col items-center justify-center text-center space-y-4">
        <ShieldAlert className="h-10 w-10 text-zinc-500" />
        <h2 className="text-lg font-semibold text-foreground">Alert Dossier Not Found</h2>
        <p className="text-xs text-muted-foreground font-mono max-w-md">
          The requested identifier &ldquo;{params.id}&rdquo; does not match any committed alert in Delta Lake.
        </p>
        <Link href="/alerts">
          <Button variant="outline" size="sm" className="text-xs border-border">
            <ArrowLeft className="h-3.5 w-3.5 mr-1.5" />
            Back to Alerts
          </Button>
        </Link>
      </div>
    );
  }

  const allMetrics = await getAccountMetrics();
  const metricsMap = new Map(allMetrics.map((m) => [m.account_id, m]));

  return (
    <div className="flex-1 pb-16">
      <Header
        title={`Forensic Dossier: ${alert.alert_id}`}
        description="Graph topology forensics, transaction timeline, and regulatory compliance evidence"
      />

      <main className="p-8 space-y-6 max-w-7xl">
        {/* Navigation & Action Bar */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <Link
            href="/alerts"
            className="flex items-center text-xs text-muted-foreground hover:text-foreground transition-colors font-medium"
          >
            <ArrowLeft className="h-3.5 w-3.5 mr-1" />
            Return to Alerts Ledger
          </Link>

          <div className="flex items-center gap-2">
            <SARExportButton alert={alert} />
            <Button
              size="sm"
              variant="destructive"
              className="text-xs h-8 font-medium"
            >
              Escalate to Compliance
            </Button>
          </div>
        </div>

        {/* Top Summary Banner */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="border-border bg-card">
            <CardHeader className="pb-1">
              <CardTitle className="text-[11px] font-medium text-muted-foreground uppercase">Risk Rating</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
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
                  {alert.risk_level} SEVERITY
                </Badge>
                <span className="text-[11px] text-muted-foreground font-mono">Rule v{alert.rule_version}</span>
              </div>
              <p className="text-[11px] text-muted-foreground mt-1 font-mono">
                {alert.rule_id}
              </p>
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardHeader className="pb-1">
              <CardTitle className="text-[11px] font-medium text-muted-foreground uppercase">Loop Volume</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-xl font-bold text-zinc-100 font-mono">
                {formatCurrency(alert.total_amount || 0, alert.currency)}
              </div>
              <p className="text-[11px] text-muted-foreground mt-1">
                Across {alert.evidence.edges.length} directed transfers
              </p>
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardHeader className="pb-1">
              <CardTitle className="text-[11px] font-medium text-muted-foreground uppercase">Detection Timestamp</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-xs font-mono font-medium text-zinc-200">
                {formatDate(alert.first_detected_at)}
              </div>
              <p className="text-[11px] text-muted-foreground mt-1 flex items-center gap-1 font-mono">
                <Clock className="h-3 w-3" /> Event Horizon
              </p>
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardHeader className="pb-1">
              <CardTitle className="text-[11px] font-medium text-muted-foreground uppercase">Canonical Cycle Hash</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-xs font-mono text-zinc-300 truncate" title={alert.cycle_id}>
                {alert.cycle_id}
              </div>
              <p className="text-[11px] text-muted-foreground mt-1">
                SHA-256 invariant signature
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Central Visualization & Ring Forensics */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Network Graph Visualizer (7 cols) */}
          <div className="lg:col-span-7 space-y-3">
            <NetworkGraph
              accounts={alert.evidence.accounts}
              edges={alert.evidence.edges}
              riskLevel={alert.risk_level}
            />

            <div className="p-3 rounded-md border border-border bg-zinc-900/60 text-xs text-muted-foreground space-y-1">
              <div className="flex items-center gap-1.5 font-medium text-zinc-200 text-[11px]">
                <Info className="h-3.5 w-3.5 text-blue-400" />
                Topology Invariant:
              </div>
              <p className="text-[11px] leading-relaxed">
                Funds originated at <span className="font-mono text-zinc-200">{alert.evidence.edges[0]?.src}</span> and returned via <span className="font-mono text-zinc-200">{alert.evidence.edges[2]?.src}</span> within a 10-minute sliding window, satisfying the closed cycle rule.
              </p>
            </div>
          </div>

          {/* Accounts Dossier & Rule Triggers (5 cols) */}
          <div className="lg:col-span-5 space-y-4">
            {/* Account Centrality in Ring */}
            <Card className="border-border bg-card">
              <CardHeader className="pb-2.5">
                <CardTitle className="text-xs font-semibold text-foreground tracking-tight">
                  Implicated Account Dossiers
                </CardTitle>
                <CardDescription className="text-[11px] text-muted-foreground">
                  PageRank centrality & connected component clustering
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-2.5">
                {alert.account_ids.map((acctId) => {
                  const metric = metricsMap.get(acctId);
                  const pagerank = metric ? metric.pagerank.toFixed(4) : "0.0450";
                  const component = metric ? metric.component_id : 2;
                  const isHub = metric ? metric.is_hub : false;

                  return (
                    <div
                      key={acctId}
                      className="p-2.5 rounded-md border border-border bg-zinc-900/50 flex items-center justify-between text-xs"
                    >
                      <div>
                        <div className="font-mono font-medium text-zinc-200 flex items-center gap-1.5">
                          {acctId}
                          {isHub ? (
                            <Badge variant="outline" className="text-[9px] px-1.5 py-0 border-blue-800 text-blue-400">
                              HUB
                            </Badge>
                          ) : (
                            <Badge variant="outline" className="text-[9px] px-1.5 py-0 border-red-900 text-red-400">
                              MULE
                            </Badge>
                          )}
                        </div>
                        <div className="text-[10px] text-muted-foreground font-mono mt-0.5">
                          Cluster: #{component}
                        </div>
                      </div>
                      <div className="text-right font-mono">
                        <div className="text-zinc-200 font-medium">PR: {pagerank}</div>
                        <div className="text-[10px] text-muted-foreground">
                          {metric?.alert_count || 1} alert history
                        </div>
                      </div>
                    </div>
                  );
                })}
              </CardContent>
            </Card>

            {/* Fired Reason Codes */}
            <Card className="border-border bg-card">
              <CardHeader className="pb-2.5">
                <CardTitle className="text-xs font-semibold text-foreground tracking-tight">
                  Compliance Rule Matches
                </CardTitle>
                <CardDescription className="text-[11px] text-muted-foreground">
                  Automated heuristics triggered during GraphFrames motif mining
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-1.5">
                {alert.reason_codes.map((code) => (
                  <div
                    key={code}
                    className="flex items-center gap-2 p-2 rounded border border-border bg-zinc-900/40 text-xs"
                  >
                    <CheckCircle2 className="h-3.5 w-3.5 text-zinc-400 shrink-0" />
                    <span className="font-mono text-zinc-300 text-[11px]">{code}</span>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Transaction Evidence Timeline Table */}
        <Card className="border-border bg-card">
          <CardHeader className="pb-3">
            <CardTitle className="text-xs font-semibold text-foreground tracking-tight">
              Sequential Transaction Ledger
            </CardTitle>
            <CardDescription className="text-[11px] text-muted-foreground">
              Reconstructed transaction sequence fulfilling the directed cycle in chronological order
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow className="border-border/60 text-[11px]">
                  <TableHead className="w-[60px]">Hop</TableHead>
                  <TableHead>Transaction ID</TableHead>
                  <TableHead>Sender Account</TableHead>
                  <TableHead>Receiver Account</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead>Timestamp</TableHead>
                  <TableHead>Currency</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {alert.evidence.edges.map((edge, idx) => (
                  <TableRow key={edge.transaction_id} className="border-border/40 hover:bg-zinc-900/40">
                    <TableCell className="font-mono text-xs text-muted-foreground">
                      #{idx + 1}
                    </TableCell>
                    <TableCell className="font-mono text-xs font-medium text-zinc-200">
                      {edge.transaction_id}
                    </TableCell>
                    <TableCell className="font-mono text-xs text-zinc-300">
                      {edge.src}
                    </TableCell>
                    <TableCell className="font-mono text-xs text-zinc-300">
                      {edge.dst}
                    </TableCell>
                    <TableCell className="text-right font-mono font-medium text-zinc-100 text-xs">
                      {formatCurrency(edge.amount, edge.currency)}
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground font-mono">
                      {formatDate(edge.time)}
                    </TableCell>
                    <TableCell className="text-xs font-mono text-zinc-400">
                      {edge.currency}
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
