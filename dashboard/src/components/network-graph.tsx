"use client";

import React, { useState } from "react";
import { formatCurrency, formatDate } from "@/lib/utils";

interface Edge {
  transaction_id: string;
  src: string;
  dst: string;
  amount: number;
  currency: string;
  time: string;
}

interface NetworkGraphProps {
  accounts: string[];
  edges: Edge[];
  riskLevel?: "HIGH" | "MEDIUM" | "LOW";
}

export function NetworkGraph({ accounts, edges, riskLevel = "HIGH" }: NetworkGraphProps) {
  const [selectedEdge, setSelectedEdge] = useState<Edge | null>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  // Position nodes in an equilateral triangle layout
  const width = 640;
  const height = 440;
  const centerX = width / 2;
  const centerY = height / 2;
  const radius = 140;

  const nodePositions = accounts.reduce((acc, acct, idx) => {
    // 3 accounts at -90 deg, 30 deg, 150 deg
    const angle = (idx * (360 / Math.max(accounts.length, 3)) - 90) * (Math.PI / 180);
    acc[acct] = {
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle),
    };
    return acc;
  }, {} as Record<string, { x: number; y: number }>);

  const riskColor =
    riskLevel === "HIGH" ? "#ef4444" : riskLevel === "MEDIUM" ? "#f59e0b" : "#3b82f6";

  return (
    <div className="relative w-full overflow-hidden rounded-xl border border-border/80 bg-slate-950 p-4 shadow-2xl">
      {/* Header controls & status */}
      <div className="mb-2 flex items-center justify-between border-b border-border/40 pb-3">
        <div className="flex items-center space-x-2">
          <span className="flex h-2.5 w-2.5 relative">
            <span
              className="absolute inline-flex h-full w-full animate-ping rounded-full opacity-75"
              style={{ backgroundColor: riskColor }}
            />
            <span
              className="relative inline-flex h-2.5 w-2.5 rounded-full"
              style={{ backgroundColor: riskColor }}
            />
          </span>
          <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Directed Triangle Cycle Topology (3-Account Loop)
          </span>
        </div>
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <span className="inline-block h-2 w-2 rounded-full bg-red-500" /> Illicit Cycle
          </span>
          <span className="flex items-center gap-1">
            <span className="inline-block h-2 w-2 rounded-full bg-blue-500" /> Account Node
          </span>
        </div>
      </div>

      {/* SVG Canvas */}
      <div className="relative flex items-center justify-center">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="h-[420px] w-full max-w-[640px]"
          style={{ overflow: "visible" }}
        >
          <defs>
            {/* Arrowhead marker */}
            <marker
              id="arrow-red"
              viewBox="0 0 10 10"
              refX="22"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 1 L 10 5 L 0 9 z" fill={riskColor} />
            </marker>

            {/* Glowing filter */}
            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="4" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* Render directed edges */}
          {edges.map((edge, idx) => {
            const p1 = nodePositions[edge.src] || { x: 100, y: 100 };
            const p2 = nodePositions[edge.dst] || { x: 300, y: 300 };

            // Midpoint for amount label
            const midX = (p1.x + p2.x) / 2;
            const midY = (p1.y + p2.y) / 2;

            // Offset normal vector for curved arc
            const dx = p2.x - p1.x;
            const dy = p2.y - p1.y;
            const dist = Math.sqrt(dx * dx + dy * dy) || 1;
            const curveOffset = 25;
            const ctrlX = midX - (dy / dist) * curveOffset;
            const ctrlY = midY + (dx / dist) * curveOffset;

            const isSelected = selectedEdge?.transaction_id === edge.transaction_id;

            return (
              <g
                key={edge.transaction_id}
                className="cursor-pointer transition-all duration-200"
                onClick={() => setSelectedEdge(edge)}
              >
                {/* Arc path */}
                <path
                  d={`M ${p1.x} ${p1.y} Q ${ctrlX} ${ctrlY} ${p2.x} ${p2.y}`}
                  fill="none"
                  stroke={riskColor}
                  strokeWidth={isSelected ? 4 : 2.5}
                  strokeDasharray={isSelected ? "none" : "6,3"}
                  markerEnd="url(#arrow-red)"
                  filter="url(#glow)"
                  className="transition-all hover:stroke-white"
                />

                {/* Edge Amount Badge */}
                <g transform={`translate(${ctrlX}, ${ctrlY})`}>
                  <rect
                    x="-45"
                    y="-12"
                    width="90"
                    height="24"
                    rx="6"
                    className="fill-slate-900/90 stroke-border/70"
                  />
                  <text
                    textAnchor="middle"
                    y="4"
                    className="fill-emerald-400 text-[11px] font-bold"
                  >
                    {formatCurrency(edge.amount, edge.currency)}
                  </text>
                </g>
              </g>
            );
          })}

          {/* Render account nodes */}
          {accounts.map((acct) => {
            const pos = nodePositions[acct] || { x: 200, y: 200 };
            const isSelected = selectedNode === acct;

            return (
              <g
                key={acct}
                transform={`translate(${pos.x}, ${pos.y})`}
                className="cursor-pointer"
                onClick={() => setSelectedNode(acct)}
              >
                {/* Outer halo */}
                <circle
                  r={isSelected ? 32 : 26}
                  className="fill-blue-600/10 stroke-blue-500/40 transition-all duration-300 hover:fill-blue-500/20"
                  strokeWidth="2"
                />
                {/* Core node */}
                <circle
                  r="18"
                  className="fill-blue-900/90 stroke-blue-400 shadow-lg"
                  strokeWidth="2.5"
                />
                {/* Account Label */}
                <text
                  textAnchor="middle"
                  y="4"
                  className="fill-white text-[10px] font-bold tracking-tight pointer-events-none"
                >
                  {acct.replace("ACC-", "")}
                </text>
                {/* Full name caption */}
                <text
                  textAnchor="middle"
                  y="42"
                  className="fill-slate-300 text-[11px] font-medium"
                >
                  {acct}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {/* Selected Transaction Inspector Bar */}
      {selectedEdge && (
        <div className="mt-3 rounded-lg border border-border bg-slate-900/90 p-3 text-xs shadow-inner">
          <div className="flex items-center justify-between">
            <span className="font-semibold text-foreground">
              Selected Edge: <span className="text-primary">{selectedEdge.transaction_id}</span>
            </span>
            <span className="text-emerald-400 font-bold text-sm">
              {formatCurrency(selectedEdge.amount, selectedEdge.currency)}
            </span>
          </div>
          <div className="mt-1 grid grid-cols-3 gap-2 text-muted-foreground">
            <div>From: <strong className="text-foreground">{selectedEdge.src}</strong></div>
            <div>To: <strong className="text-foreground">{selectedEdge.dst}</strong></div>
            <div>Time: <strong className="text-foreground">{formatDate(selectedEdge.time)}</strong></div>
          </div>
        </div>
      )}
    </div>
  );
}

