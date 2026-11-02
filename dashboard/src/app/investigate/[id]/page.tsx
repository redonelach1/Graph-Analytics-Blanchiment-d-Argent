import React from "react";
import Link from "next/link";
import { notFound } from "next/navigation";
import {
  ArrowLeft,
  ShieldAlert,
  Download,
  AlertTriangle,
  Clock,
  Layers,
  CheckCircle,
  FileText,
  Share2,
  ExternalLink,
  Info
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
import { getAlertById, getAccountMetrics } from "@/lib/data-service";
import { formatCurrency, formatDate } from "@/lib/utils";

interface InvestigatePageProps {
  params: {
    id: string;
  };
}

export default async function InvestigatePage({ params }: InvestigatePageProps) {
  const alert = await getAlertById(params.id);

  if (!alert) {
    return (
      <div className="flex-1 p-12 flex flex-col items-center justify-center text-center space-y-4">
        <div className="p-4 rounded-full bg-red-500/10 text-red-400">
          <ShieldAlert className="h-10 w-10" />
        </div>
        <h2 className="text-xl font-bold text-foreground">Alert Not Found</h2>
        <p className="text-sm text-muted-foreground max-w-md">
          The alert ID <span className="font-mono text-primary font-semibold">{params.id}</span> does not exist in the active Delta Lake fraud store.
        </p>
        <Link href="/alerts">
          <Button variant="outline" size="sm">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Return to Alerts
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
        title={`Investigation Dossier: ${alert.alert_id}`}
        description="Graph topology forensics, transaction timeline, and regulatory compliance evidence"
      />

      <main className="p-8 space-y-8 max-w-7xl">
        {/* Navigation & Action Bar */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <Link
            href="/alerts"
            className="flex items-center text-xs font-semibold text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="h-4 w-4 mr-1.5" />
            Back to Alerts Directory
          </Link>

          <div className="flex items-center gap-2.5">
            <Button
              variant="outline"
              size="sm"
              className="text-xs h-8 bg-slate-900 border-border/80"
              onClick={undefined}
            >
              <Download className="h-3.5 w-3.5 mr-1.5 text-blue-400" />
              Download SAR JSON
            </Button>
            <Button
              size="sm"
              className="text-xs h-8 bg-red-600 hover:bg-red-500 text-white shadow-sm shadow-red-500/20"
            >
              <AlertTriangle className="h-3.5 w-3.5 mr-1.5" />
              Escalate to Compliance
            </Button>
          </div>
        </div>

        {/* Top Summary Banner */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="bg-slate-900/60 border-border/60">
            <CardHeader className="pb-1">
              <CardTitle className="text-xs font-semibold text-muted-foreground uppercase">Risk Rating</CardTitle>
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
                  className="text-xs px-2.5 py-0.5"
                >
                  {alert.risk_level} RISK
                </Badge>
                <span className="text-xs text-muted-foreground">Rule v{alert.rule_version}</span>
              </div>
              <p className="text-[11px] text-muted-foreground mt-1">Rule: {alert.rule_id}</p>
            </CardContent>
          </Card>

          <Card className="bg-slate-900/60 border-border/60">
            <CardHeader className="pb-1">
              <CardTitle className="text-xs font-semibold text-muted-foreground uppercase">Flagged Loop Volume</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-xl font-bold text-emerald-400 font-mono">
                {formatCurrency(alert.total_amount || 0, alert.currency)}
              </div>
              <p className="text-[11px] text-muted-foreground mt-1">
                Across {alert.evidence.edges.length} directed transfers
              </p>
            </CardContent>
          </Card>

          <Card className="bg-slate-900/60 border-border/60">
            <CardHeader className="pb-1">
              <CardTitle className="text-xs font-semibold text-muted-foreground uppercase">Detection Timestamp</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-sm font-semibold text-foreground">
                {formatDate(alert.first_detected_at)}
              </div>
              <p className="text-[11px] text-muted-foreground mt-1 flex items-center gap-1">
                <Clock className="h-3 w-3" /> Event Time Window
              </p>
            </CardContent>
          </Card>

          <Card className="bg-slate-900/60 border-border/60">
            <CardHeader className="pb-1">
              <CardTitle className="text-xs font-semibold text-muted-foreground uppercase">Canonical Cycle ID</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-xs font-mono font-semibold text-blue-400 truncate">
                {alert.cycle_id}
              </div>
              <p className="text-[11px] text-muted-foreground mt-1">
                Invariant SHA256 ring fingerprint
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Central Visualization & Ring Forensics */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Network Graph Visualizer (7 cols) */}
          <div className="lg:col-span-7 space-y-4">
            <div>
              <h3 className="text-sm font-bold uppercase tracking-wider text-foreground">
                Directed Cycle Topology
              </h3>
              <p className="text-xs text-muted-foreground">
                GraphFrames motif match: (a)-[e1]-&gt;(b); (b)-[e2]-&gt;(c); (c)-[e3]-&gt;(a)
              </p>
            </div>

            <NetworkGraph
              accounts={alert.evidence.accounts}
              edges={alert.evidence.edges}
              riskLevel={alert.risk_level}
            />

            <div className="p-3.5 rounded-lg border border-border/60 bg-slate-900/40 text-xs text-muted-foreground space-y-1">
              <div className="flex items-center gap-1.5 font-semibold text-foreground">
                <Info className="h-3.5 w-3.5 text-blue-400" />
                Topology Invariant:
              </div>
              <p>
                This directed triangle completes an illicit layering loop where funds originated at{" "}
                <span className="font-mono text-primary font-medium">{alert.evidence.edges[0]?.src}</span> and returned via{" "}
                <span className="font-mono text-primary font-medium">{alert.evidence.edges[2]?.src}</span> within a 10-minute sliding window.
              </p>
            </div>
          </div>

          {/* Accounts Dossier & Rule Triggers (5 cols) */}
          <div className="lg:col-span-5 space-y-6">
            {/* Account Centrality in Ring */}
            <Card className="bg-slate-900/60 border-border/60">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-bold text-foreground">
                  Involved Account Dossiers
                </CardTitle>
                <CardDescription className="text-xs">
                  PageRank centrality & connected component clustering
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {alert.account_ids.map((acctId) => {
                  const metric = metricsMap.get(acctId);
                  const pagerank = metric ? metric.pagerank.toFixed(4) : "0.0450";
                  const component = metric ? metric.component_id : 2;
                  const isHub = metric ? metric.is_hub : false;

                  return (
                    <div
                      key={acctId}
                      className="p-3 rounded-lg border border-border/60 bg-slate-950/60 flex items-center justify-between"
                    >
                      <div>
                        <div className="font-mono text-xs font-bold text-foreground flex items-center gap-1.5">
                          {acctId}
                          {isHub ? (
                            <Badge variant="outline" className="text-[9px] px-1.5 py-0 border-blue-500/40 text-blue-400">
                              HUB
                            </Badge>
                          ) : (
                            <Badge variant="outline" className="text-[9px] px-1.5 py-0 border-red-500/40 text-red-400">
                              MULE
                            </Badge>
                          )}
                        </div>
                        <div className="text-[11px] text-muted-foreground mt-0.5">
                          Cluster ID: <span className="font-mono font-medium text-slate-300">#{component}</span>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-xs font-mono font-semibold text-blue-400">
                          PR: {pagerank}
                        </div>
                        <div className="text-[10px] text-muted-foreground">
                          {metric?.alert_count || 1} prior alerts
                        </div>
                      </div>
                    </div>
                  );
                })}
              </CardContent>
            </Card>

            {/* Fired Reason Codes */}
            <Card className="bg-slate-900/60 border-border/60">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-bold text-foreground">
                  Compliance Reason Codes
                </CardTitle>
                <CardDescription className="text-xs">
                  Automated heuristics triggered during batch motif execution
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                {alert.reason_codes.map((code) => (
                  <div
                    key={code}
                    className="flex items-center gap-2 p-2 rounded-md bg-slate-950/80 border border-border/60 text-xs"
                  >
                    <CheckCircle className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
                    <span className="font-mono text-slate-300 font-medium">{code}</span>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Transaction Evidence Timeline Table */}
        <Card className="bg-slate-900/60 border-border/60">
          <CardHeader>
            <CardTitle className="text-sm font-bold text-foreground">
              Sequential Transaction Evidence Flow
            </CardTitle>
            <CardDescription className="text-xs">
              Reconstructed transaction sequence fulfilling the directed cycle in chronological order
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader className="bg-slate-950/80">
                <TableRow className="border-border/60">
                  <TableHead className="w-[80px] text-xs">Hop</TableHead>
                  <TableHead className="text-xs">Transaction ID</TableHead>
                  <TableHead className="text-xs">Sender (Src)</TableHead>
                  <TableHead className="text-xs">Receiver (Dst)</TableHead>
                  <TableHead className="text-xs text-right">Amount</TableHead>
                  <TableHead className="text-xs">Event Timestamp</TableHead>
                  <TableHead className="text-xs">Currency</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {alert.evidence.edges.map((edge, idx) => (
                  <TableRow key={edge.transaction_id} className="border-border/40 hover:bg-slate-800/40">
                    <TableCell className="font-mono text-xs font-semibold text-blue-400">
                      #{idx + 1}
                    </TableCell>
                    <TableCell className="font-mono text-xs font-medium text-foreground">
                      {edge.transaction_id}
                    </TableCell>
                    <TableCell className="font-mono text-xs text-slate-300">
                      {edge.src}
                    </TableCell>
                    <TableCell className="font-mono text-xs text-slate-300">
                      {edge.dst}
                    </TableCell>
                    <TableCell className="text-right font-mono font-bold text-emerald-400 text-xs">
                      {formatCurrency(edge.amount, edge.currency)}
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground font-mono">
                      {formatDate(edge.time)}
                    </TableCell>
                    <TableCell className="text-xs font-semibold text-slate-400">
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
