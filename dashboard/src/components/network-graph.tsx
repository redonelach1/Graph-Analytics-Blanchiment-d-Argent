"use client";

import React, { useState } from "react";
import { formatCurrency, formatDate } from "@/lib/utils";
import { ArrowRight, Info } from "lucide-react";

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
  const height = 400;
  const centerX = width / 2;
  const centerY = height / 2;
  const radius = 135;

  const nodePositions = accounts.reduce((acc, acct, idx) => {
    // 3 accounts at -90 deg, 30 deg, 150 deg
    const angle = (idx * (360 / Math.max(accounts.length, 3)) - 90) * (Math.PI / 180);
    acc[acct] = {
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle),
    };
    return acc;
  }, {} as Record<string, { x: number; y: number }>);

  // Theme-tailored crisp stroke colors
  const strokeColor =
    riskLevel === "HIGH" ? "#f87171" : riskLevel === "MEDIUM" ? "#fbbf24" : "#60a5fa";

  return (
    <div className="w-full rounded-lg border border-border bg-card p-5">
      {/* Header controls & status */}
      <div className="flex items-center justify-between border-b border-border/60 pb-3">
        <div className="flex items-center space-x-2">
          <span
            className="h-2 w-2 rounded-full"
            style={{ backgroundColor: strokeColor }}
          />
          <span className="text-xs font-medium text-foreground tracking-tight">
            Directed Triangle Cycle Topology ($A \to B \to C \to A$)
          </span>
        </div>
        <div className="flex items-center gap-4 text-[11px] text-muted-foreground">
          <span className="flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: strokeColor }} />
            Transfer Edge
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-blue-400" />
            Account Node
          </span>
        </div>
      </div>

      {/* SVG Canvas */}
      <div className="relative flex items-center justify-center py-2">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="h-[360px] w-full max-w-[620px]"
          style={{ overflow: "visible" }}
        >
          <defs>
            {/* Arrowhead marker */}
            <marker
              id={`arrow-${riskLevel}`}
              viewBox="0 0 10 10"
              refX="26"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 1.5 L 9 5 L 0 8.5 z" fill={strokeColor} />
            </marker>
          </defs>

          {/* Render directed edges */}
          {edges.map((edge) => {
            const p1 = nodePositions[edge.src] || { x: 120, y: 120 };
            const p2 = nodePositions[edge.dst] || { x: 320, y: 320 };

            // Midpoint
            const midX = (p1.x + p2.x) / 2;
            const midY = (p1.y + p2.y) / 2;

            // Curved arc offset
            const dx = p2.x - p1.x;
            const dy = p2.y - p1.y;
            const dist = Math.sqrt(dx * dx + dy * dy) || 1;
            const curveOffset = 24;
            const ctrlX = midX - (dy / dist) * curveOffset;
            const ctrlY = midY + (dx / dist) * curveOffset;

            const isSelected = selectedEdge?.transaction_id === edge.transaction_id;

            return (
              <g
                key={edge.transaction_id}
                className="cursor-pointer transition-opacity"
                onClick={() => {
                  setSelectedEdge(isSelected ? null : edge);
                  setSelectedNode(null);
                }}
              >
                {/* Clickable wider hover target */}
                <path
                  d={`M ${p1.x} ${p1.y} Q ${ctrlX} ${ctrlY} ${p2.x} ${p2.y}`}
                  fill="none"
                  stroke="transparent"
                  strokeWidth={16}
                />

                {/* Visible Crisp Arc */}
                <path
                  d={`M ${p1.x} ${p1.y} Q ${ctrlX} ${ctrlY} ${p2.x} ${p2.y}`}
                  fill="none"
                  stroke={isSelected ? "#ffffff" : strokeColor}
                  strokeWidth={isSelected ? 2.5 : 1.75}
                  strokeDasharray={isSelected ? undefined : "5 3"}
                  markerEnd={`url(#arrow-${riskLevel})`}
                  className="transition-colors duration-150"
                />

                {/* Amount Pill */}
                <g transform={`translate(${ctrlX}, ${ctrlY})`}>
                  <rect
                    x="-48"
                    y="-11"
                    width="96"
                    height="22"
                    rx="4"
                    className="fill-zinc-900 stroke-zinc-800"
                    strokeWidth="1"
                  />
                  <text
                    textAnchor="middle"
                    y="4"
                    className="fill-zinc-100 text-[11px] font-mono font-medium"
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
                onClick={() => {
                  setSelectedNode(isSelected ? null : acct);
                  setSelectedEdge(null);
                }}
              >
                {/* Crisp outer ring on selection */}
                {isSelected && (
                  <circle
                    r="24"
                    fill="none"
                    stroke="#3b82f6"
                    strokeWidth="1.5"
                    strokeDasharray="3 3"
                  />
                )}

                {/* Core node */}
                <circle
                  r="18"
                  className="fill-zinc-900 stroke-zinc-700 hover:stroke-zinc-500 transition-colors"
                  strokeWidth="1.5"
                />

                {/* Account identifier abbreviation */}
                <text
                  textAnchor="middle"
                  y="4"
                  className="fill-zinc-200 text-[10px] font-mono font-semibold pointer-events-none"
                >
                  {acct.replace("ACC-", "")}
                </text>

                {/* Full name label */}
                <text
                  textAnchor="middle"
                  y="34"
                  className="fill-zinc-400 text-[11px] font-mono tracking-tight"
                >
                  {acct}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {/* Selected Inspector Ledger Panel */}
      {selectedEdge ? (
        <div className="mt-2 rounded-md border border-border bg-zinc-900/60 p-3 text-xs">
          <div className="flex items-center justify-between pb-1.5 border-b border-border/40">
            <span className="font-mono text-zinc-300 font-medium flex items-center gap-1.5">
              <span>Transfer:</span>
              <span className="text-white">{selectedEdge.transaction_id}</span>
            </span>
            <span className="font-mono font-semibold text-emerald-400">
              {formatCurrency(selectedEdge.amount, selectedEdge.currency)}
            </span>
          </div>
          <div className="mt-2 grid grid-cols-3 gap-2 text-muted-foreground font-mono text-[11px]">
            <div>From: <span className="text-zinc-200">{selectedEdge.src}</span></div>
            <div className="flex items-center gap-1">
              <span>To:</span>
              <span className="text-zinc-200">{selectedEdge.dst}</span>
            </div>
            <div>Time: <span className="text-zinc-200">{formatDate(selectedEdge.time)}</span></div>
          </div>
        </div>
      ) : selectedNode ? (
        <div className="mt-2 rounded-md border border-border bg-zinc-900/60 p-3 text-xs flex items-center justify-between">
          <span className="font-mono text-zinc-300">
            Selected Entity: <strong className="text-white">{selectedNode}</strong>
          </span>
          <span className="text-muted-foreground text-[11px]">
            Participates in 2 cycle edges in this window
          </span>
        </div>
      ) : (
        <div className="mt-2 text-center text-[11px] text-muted-foreground py-1">
          Click on any transfer arc or account node to inspect ledger details.
        </div>
      )}
    </div>
  );
}
