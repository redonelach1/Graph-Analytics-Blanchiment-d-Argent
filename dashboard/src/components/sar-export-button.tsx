"use client";

import React from "react";
import { Download, Check } from "lucide-react";
import { Button } from "@/components/ui/button";

interface SARExportButtonProps {
  alert: any;
}

export function SARExportButton({ alert }: SARExportButtonProps) {
  const [downloaded, setDownloaded] = React.useState(false);

  const handleDownload = () => {
    const sarData = {
      regulatory_standard: "FATF-AML-SAR-V1",
      generated_at: new Date().toISOString(),
      report_classification: "CONFIDENTIAL / REGULATORY COMPLIANCE",
      alert_dossier: {
        alert_id: alert.alert_id,
        canonical_cycle_id: alert.cycle_id,
        rule_identifier: alert.rule_id,
        rule_version: alert.rule_version,
        risk_level: alert.risk_level,
        flagged_volume_mad: alert.total_amount,
        detection_timestamp: alert.first_detected_at,
        time_window: alert.evidence?.matching_window || {
          start: alert.event_min,
          end: alert.event_max,
        },
        implicated_entities: alert.account_ids,
        reason_codes: alert.reason_codes,
        transaction_ledger: alert.evidence?.edges || [],
      },
    };

    const blob = new Blob([JSON.stringify(sarData, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `SAR_${alert.alert_id}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    setDownloaded(true);
    setTimeout(() => setDownloaded(false), 2500);
  };

  return (
    <Button
      variant="outline"
      size="sm"
      className="h-8 text-xs gap-1.5 font-medium border-border hover:bg-zinc-800"
      onClick={handleDownload}
    >
      {downloaded ? (
        <>
          <Check className="h-3.5 w-3.5 text-emerald-400" />
          <span>Exported</span>
        </>
      ) : (
        <>
          <Download className="h-3.5 w-3.5 text-zinc-400" />
          <span>Export SAR JSON</span>
        </>
      )}
    </Button>
  );
}
