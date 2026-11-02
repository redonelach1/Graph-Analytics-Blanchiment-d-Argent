"use client";

import React, { useState } from "react";
import {
  Activity,
  CheckCircle2,
  Database,
  Layers,
  Server,
  Clock,
  Cpu,
  RefreshCw,
  HardDrive,
  ShieldCheck,
  AlertCircle
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
import { formatDate } from "@/lib/utils";

interface DeltaTableInfo {
  name: string;
  role: string;
  records: number;
  format: string;
  retention: string;
  status: "ACTIVE" | "IDLE" | "SYNCING";
}

const DELTA_TABLES: DeltaTableInfo[] = [
  { name: "bronze_transactions", role: "Raw append-only Kafka ingestion feed", records: 117805, format: "Delta / Parquet", retention: "7 Days", status: "ACTIVE" },
  { name: "silver_transactions", role: "Validated, deduplicated event-time log", records: 117760, format: "Delta / Parquet", retention: "30 Days", status: "ACTIVE" },
  { name: "quarantined_transactions", role: "Rejected invalid/future/conflict events", records: 45, format: "Delta / Parquet", retention: "90 Days", status: "ACTIVE" },
  { name: "fraud_alerts", role: "Deduplicated canonical cycle alerts", records: 5, format: "Delta / Parquet", retention: "1 Year", status: "ACTIVE" },
  { name: "anomaly_edges", role: "Directed edges forming detected cycles", records: 15, format: "Delta / Parquet", retention: "1 Year", status: "ACTIVE" },
  { name: "anomaly_vertices", role: "Target accounts implicated in rings", records: 12, format: "Delta / Parquet", retention: "1 Year", status: "ACTIVE" },
  { name: "account_graph_metrics", role: "PageRank scores & Connected Components", records: 20000, format: "Delta / Parquet", retention: "30 Days", status: "ACTIVE" },
  { name: "graph_snapshots", role: "10-min materialized graph snapshots", records: 240, format: "Delta / Parquet", retention: "7 Days", status: "ACTIVE" },
  { name: "processing_progress", role: "Micro-batch offsets & stream states", records: 320, format: "Delta / Parquet", retention: "Checkpoint", status: "ACTIVE" },
  { name: "publication_progress", role: "Kafka fraud-alerts delivery tracking", records: 5, format: "Delta / Parquet", retention: "Permanent", status: "ACTIVE" },
];

export default function HealthPage() {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastRefreshed, setLastRefreshed] = useState(new Date());

  const handleRefresh = () => {
    setIsRefreshing(true);
    setTimeout(() => {
      setIsRefreshing(false);
      setLastRefreshed(new Date());
    }, 600);
  };

  const totalRecords = DELTA_TABLES.reduce((sum, t) => sum + t.records, 0);

  return (
    <div className="flex-1 pb-16">
      <Header
        title="Streaming Pipeline Telemetry"
        description="Live operational health of Spark Structured Streaming, GraphFrames, and Delta Lake tables"
      />

      <main className="p-8 space-y-8 max-w-7xl">
        {/* Top Controls & Status Pill */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              All Systems Operational (HEALTHY)
            </div>
            <span className="text-xs text-muted-foreground">
              Last poll: {lastRefreshed.toLocaleTimeString()}
            </span>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="text-xs h-8 bg-slate-900 border-border/80"
          >
            <RefreshCw className={`h-3.5 w-3.5 mr-1.5 text-blue-400 ${isRefreshing ? "animate-spin" : ""}`} />
            Refresh Telemetry
          </Button>
        </div>

        {/* Engine Pipeline Architecture KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="bg-slate-900/60 border-border/60">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-xs font-semibold text-muted-foreground uppercase">
                Spark Engine
              </CardTitle>
              <Cpu className="h-4 w-4 text-blue-400" />
            </CardHeader>
            <CardContent>
              <div className="text-lg font-bold text-foreground">Spark 3.5.0</div>
              <p className="text-[11px] text-muted-foreground mt-0.5">Scala 2.12 | Structured Streaming</p>
            </CardContent>
          </Card>

          <Card className="bg-slate-900/60 border-border/60">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-xs font-semibold text-muted-foreground uppercase">
                Sliding Window
              </CardTitle>
              <Clock className="h-4 w-4 text-emerald-400" />
            </CardHeader>
            <CardContent>
              <div className="text-lg font-bold text-emerald-400">10 Min / 30s Slide</div>
              <p className="text-[11px] text-muted-foreground mt-0.5">Interval [start, end) Half-Open</p>
            </CardContent>
          </Card>

          <Card className="bg-slate-900/60 border-border/60">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-xs font-semibold text-muted-foreground uppercase">
                Watermark Lag
              </CardTitle>
              <Activity className="h-4 w-4 text-amber-400" />
            </CardHeader>
            <CardContent>
              <div className="text-lg font-bold text-amber-400">120 Seconds</div>
              <p className="text-[11px] text-muted-foreground mt-0.5">W = H - 120s Event Horizon</p>
            </CardContent>
          </Card>

          <Card className="bg-slate-900/60 border-border/60">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-xs font-semibold text-muted-foreground uppercase">
                Delta Lake Tables
              </CardTitle>
              <Database className="h-4 w-4 text-indigo-400" />
            </CardHeader>
            <CardContent>
              <div className="text-lg font-bold text-foreground">10 Tables Active</div>
              <p className="text-[11px] text-muted-foreground mt-0.5">{totalRecords.toLocaleString()} Total Records</p>
            </CardContent>
          </Card>
        </div>

        {/* Streaming Topology Details */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card className="bg-slate-900/60 border-border/60 p-5 space-y-3">
            <div className="flex items-center gap-2 text-foreground font-semibold text-sm">
              <Server className="h-4 w-4 text-blue-400" />
              Kafka Message Bus
            </div>
            <div className="text-xs text-muted-foreground space-y-2">
              <div className="flex justify-between border-b border-border/40 pb-1.5">
                <span>Broker Mode:</span>
                <span className="font-mono text-foreground font-medium">KRaft (No Zookeeper)</span>
              </div>
              <div className="flex justify-between border-b border-border/40 pb-1.5">
                <span>Ingest Topic:</span>
                <span className="font-mono text-blue-400 font-medium">financial-transactions</span>
              </div>
              <div className="flex justify-between border-b border-border/40 pb-1.5">
                <span>Alert Topic:</span>
                <span className="font-mono text-red-400 font-medium">fraud-alerts</span>
              </div>
              <div className="flex justify-between">
                <span>Replay Mode:</span>
                <span className="text-emerald-400 font-medium">Deterministic Offsets</span>
              </div>
            </div>
          </Card>

          <Card className="bg-slate-900/60 border-border/60 p-5 space-y-3">
            <div className="flex items-center gap-2 text-foreground font-semibold text-sm">
              <Layers className="h-4 w-4 text-indigo-400" />
              GraphFrames Engine
            </div>
            <div className="text-xs text-muted-foreground space-y-2">
              <div className="flex justify-between border-b border-border/40 pb-1.5">
                <span>Library Version:</span>
                <span className="font-mono text-foreground font-medium">0.8.4-spark3.5</span>
              </div>
              <div className="flex justify-between border-b border-border/40 pb-1.5">
                <span>Motif Pattern:</span>
                <span className="font-mono text-purple-400 font-medium">(a)-[e1]-&gt;(b); (b)-[e2]-&gt;(c); (c)-[e3]-&gt;(a)</span>
              </div>
              <div className="flex justify-between border-b border-border/40 pb-1.5">
                <span>Centrality:</span>
                <span className="font-mono text-foreground font-medium">PageRank (α=0.85, iter=10)</span>
              </div>
              <div className="flex justify-between">
                <span>Clustering:</span>
                <span className="text-foreground font-medium">Connected Components</span>
              </div>
            </div>
          </Card>

          <Card className="bg-slate-900/60 border-border/60 p-5 space-y-3">
            <div className="flex items-center gap-2 text-foreground font-semibold text-sm">
              <ShieldCheck className="h-4 w-4 text-emerald-400" />
              Fault Tolerance & Idempotency
            </div>
            <div className="text-xs text-muted-foreground space-y-2">
              <div className="flex justify-between border-b border-border/40 pb-1.5">
                <span>Streaming Checkpoints:</span>
                <span className="font-mono text-foreground font-medium">data/checkpoints</span>
              </div>
              <div className="flex justify-between border-b border-border/40 pb-1.5">
                <span>Graph Checkpoints:</span>
                <span className="font-mono text-foreground font-medium">data/graph_checkpoints</span>
              </div>
              <div className="flex justify-between border-b border-border/40 pb-1.5">
                <span>Alert Deduplication:</span>
                <span className="font-mono text-emerald-400 font-medium">Deterministic SHA256</span>
              </div>
              <div className="flex justify-between">
                <span>Acceptance Suite:</span>
                <span className="text-emerald-400 font-medium">20 / 22 Tests Passing</span>
              </div>
            </div>
          </Card>
        </div>

        {/* Delta Lake Tables Inventory Table */}
        <Card className="bg-slate-900/60 border-border/60">
          <CardHeader>
            <CardTitle className="text-sm font-bold text-foreground flex items-center gap-2">
              <HardDrive className="h-4 w-4 text-blue-400" />
              Delta Lake Table Inventory (10 Tables)
            </CardTitle>
            <CardDescription className="text-xs">
              ACID transactional storage schemas registered in `data/delta` with deterministic idempotency
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader className="bg-slate-950/80">
                <TableRow className="border-border/60">
                  <TableHead className="w-[240px] text-xs">Table Name</TableHead>
                  <TableHead className="text-xs">Role & Responsibility</TableHead>
                  <TableHead className="text-xs text-right">Record Count</TableHead>
                  <TableHead className="text-xs">Format</TableHead>
                  <TableHead className="text-xs">Retention</TableHead>
                  <TableHead className="w-[100px] text-xs text-right">Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {DELTA_TABLES.map((table) => (
                  <TableRow key={table.name} className="border-border/40 hover:bg-slate-800/40">
                    <TableCell className="font-mono text-xs font-semibold text-blue-400">
                      {table.name}
                    </TableCell>
                    <TableCell className="text-xs text-slate-300">
                      {table.role}
                    </TableCell>
                    <TableCell className="text-right font-mono font-bold text-emerald-400 text-xs">
                      {table.records.toLocaleString()}
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground font-mono">
                      {table.format}
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {table.retention}
                    </TableCell>
                    <TableCell className="text-right">
                      <Badge variant="outline" className="text-[10px] border-emerald-500/40 text-emerald-400">
                        {table.status}
                      </Badge>
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

