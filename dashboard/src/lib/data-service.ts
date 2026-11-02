/**
 * data-service.ts — Data Access Layer for Next.js Dashboard.
 * Reads alerts, metrics, and health telemetry from Delta tables or active pipeline state.
 */

export interface FraudAlert {
  alert_id: string;
  cycle_id: string;
  rule_id: string;
  rule_version: number;
  risk_level: "HIGH" | "MEDIUM" | "LOW";
  reason_codes: string[];
  account_ids: string[];
  transaction_ids: string[];
  currency: string;
  first_detected_at: string;
  event_min: string;
  event_max: string;
  total_amount?: number;
  evidence: {
    accounts: string[];
    edges: Array<{
      transaction_id: string;
      src: string;
      dst: string;
      amount: number;
      currency: string;
      time: string;
    }>;
    matching_window?: {
      start: string;
      end: string;
    };
  };
}

export interface AccountMetric {
  account_id: string;
  pagerank: number;
  component_id: number;
  alert_count: number;
  total_volume: number;
  is_hub: boolean;
}

export interface PipelineHealth {
  status: "HEALTHY" | "DEGRADED" | "IDLE";
  last_batch_time: string;
  high_water_mark: string;
  transactions_ingested: number;
  active_alerts: number;
  tables: {
    bronze_transactions: number;
    silver_transactions: number;
    quarantined_transactions: number;
    fraud_alerts: number;
    account_graph_metrics: number;
  };
}

// Sample fallback dataset matching exact Phase 4 / Phase 5 outputs for instant visualization
const MOCK_ALERTS: FraudAlert[] = [
  {
    alert_id: "ALT-7D29F4C1B039A8E2",
    cycle_id: "CYC-9B14E2F3A8C7",
    rule_id: "TEMPORAL_TRIANGLE",
    rule_version: 1,
    risk_level: "HIGH",
    reason_codes: ["DIRECTED_TRIANGLE", "SAME_CURRENCY", "HIGH_VALUE_THRESHOLD_MET", "AMOUNT_RATIO_TOLERANT_1.08"],
    account_ids: ["ACC-0081", "ACC-0014", "ACC-0003"],
    transaction_ids: ["TXN-64CAB8C7BF32", "TXN-E7D6A14A8A5F", "TXN-B55D9821222B"],
    currency: "MAD",
    first_detected_at: "2026-11-02 19:08:16",
    event_min: "2026-11-02 19:08:15",
    event_max: "2026-11-02 19:12:34",
    total_amount: 463859.44,
    evidence: {
      accounts: ["ACC-0081", "ACC-0014", "ACC-0003"],
      edges: [
        { transaction_id: "TXN-64CAB8C7BF32", src: "ACC-0081", dst: "ACC-0014", amount: 161232.57, currency: "MAD", time: "2026-11-02T19:08:15Z" },
        { transaction_id: "TXN-E7D6A14A8A5F", src: "ACC-0014", dst: "ACC-0003", amount: 154750.32, currency: "MAD", time: "2026-11-02T19:09:11Z" },
        { transaction_id: "TXN-B55D9821222B", src: "ACC-0003", dst: "ACC-0081", amount: 147876.55, currency: "MAD", time: "2026-11-02T19:12:34Z" },
      ],
      matching_window: { start: "2026-11-02T19:05:00Z", end: "2026-11-02T19:15:00Z" }
    }
  },
  {
    alert_id: "ALT-3C89B102A4E7F912",
    cycle_id: "CYC-4A29E8D102C3",
    rule_id: "TEMPORAL_TRIANGLE",
    rule_version: 1,
    risk_level: "MEDIUM",
    reason_codes: ["DIRECTED_TRIANGLE", "SAME_CURRENCY", "MEDIUM_VALUE_THRESHOLD_MET"],
    account_ids: ["ACC-0012", "ACC-0045", "ACC-0089"],
    transaction_ids: ["TXN-1A2B3C4D5E6F", "TXN-7G8H9I0J1K2L", "TXN-3M4N5O6P7Q8R"],
    currency: "MAD",
    first_detected_at: "2026-11-02 18:45:22",
    event_min: "2026-11-02 18:41:00",
    event_max: "2026-11-02 18:44:30",
    total_amount: 87400.00,
    evidence: {
      accounts: ["ACC-0012", "ACC-0045", "ACC-0089"],
      edges: [
        { transaction_id: "TXN-1A2B3C4D5E6F", src: "ACC-0012", dst: "ACC-0045", amount: 30000.00, currency: "MAD", time: "2026-11-02T18:41:00Z" },
        { transaction_id: "TXN-7G8H9I0J1K2L", src: "ACC-0045", dst: "ACC-0089", amount: 29000.00, currency: "MAD", time: "2026-11-02T18:42:45Z" },
        { transaction_id: "TXN-3M4N5O6P7Q8R", src: "ACC-0089", dst: "ACC-0012", amount: 28400.00, currency: "MAD", time: "2026-11-02T18:44:30Z" },
      ],
      matching_window: { start: "2026-11-02T18:40:00Z", end: "2026-11-02T18:50:00Z" }
    }
  },
  {
    alert_id: "ALT-E1A7D0924C58B331",
    cycle_id: "CYC-1F08C23A9E71",
    rule_id: "TEMPORAL_TRIANGLE",
    rule_version: 1,
    risk_level: "LOW",
    reason_codes: ["DIRECTED_TRIANGLE", "SAME_CURRENCY", "LOW_VALUE_CYCLE"],
    account_ids: ["ACC-0021", "ACC-0067", "ACC-0034"],
    transaction_ids: ["TXN-9A8B7C6D5E4F", "TXN-3G2H1I0J9K8L", "TXN-5M6N7O8P9Q0R"],
    currency: "MAD",
    first_detected_at: "2026-11-02 17:12:05",
    event_min: "2026-11-02 17:08:10",
    event_max: "2026-11-02 17:11:40",
    total_amount: 14200.00,
    evidence: {
      accounts: ["ACC-0021", "ACC-0067", "ACC-0034"],
      edges: [
        { transaction_id: "TXN-9A8B7C6D5E4F", src: "ACC-0021", dst: "ACC-0067", amount: 5000.00, currency: "MAD", time: "2026-11-02T17:08:10Z" },
        { transaction_id: "TXN-3G2H1I0J9K8L", src: "ACC-0067", dst: "ACC-0034", amount: 4800.00, currency: "MAD", time: "2026-11-02T17:09:55Z" },
        { transaction_id: "TXN-5M6N7O8P9Q0R", src: "ACC-0034", dst: "ACC-0021", amount: 4400.00, currency: "MAD", time: "2026-11-02T17:11:40Z" },
      ],
      matching_window: { start: "2026-11-02T17:05:00Z", end: "2026-11-02T17:15:00Z" }
    }
  },
  {
    alert_id: "ALT-5B81C40D9E12FA47",
    cycle_id: "CYC-AML-20K-042",
    rule_id: "TEMPORAL_TRIANGLE",
    rule_version: 1,
    risk_level: "HIGH",
    reason_codes: ["DIRECTED_TRIANGLE", "SAME_CURRENCY", "HIGH_VALUE_THRESHOLD_MET", "RAPID_DISPERSAL"],
    account_ids: ["ACC-0105", "ACC-0312", "ACC-0789"],
    transaction_ids: ["TXN-AML-0042A", "TXN-AML-0042B", "TXN-AML-0042C"],
    currency: "MAD",
    first_detected_at: "2026-11-02 16:30:15",
    event_min: "2026-11-02 16:26:00",
    event_max: "2026-11-02 16:29:45",
    total_amount: 620000.00,
    evidence: {
      accounts: ["ACC-0105", "ACC-0312", "ACC-0789"],
      edges: [
        { transaction_id: "TXN-AML-0042A", src: "ACC-0105", dst: "ACC-0312", amount: 215000.00, currency: "MAD", time: "2026-11-02T16:26:00Z" },
        { transaction_id: "TXN-AML-0042B", src: "ACC-0312", dst: "ACC-0789", amount: 205000.00, currency: "MAD", time: "2026-11-02T16:28:10Z" },
        { transaction_id: "TXN-AML-0042C", src: "ACC-0789", dst: "ACC-0105", amount: 200000.00, currency: "MAD", time: "2026-11-02T16:29:45Z" },
      ],
      matching_window: { start: "2026-11-02T16:25:00Z", end: "2026-11-02T16:35:00Z" }
    }
  },
  {
    alert_id: "ALT-9D44F2A1E8B07C33",
    cycle_id: "CYC-AML-20K-118",
    rule_id: "TEMPORAL_TRIANGLE",
    rule_version: 1,
    risk_level: "MEDIUM",
    reason_codes: ["DIRECTED_TRIANGLE", "SAME_CURRENCY", "MEDIUM_VALUE_THRESHOLD_MET"],
    account_ids: ["ACC-0055", "ACC-0062", "ACC-0071"],
    transaction_ids: ["TXN-AML-0118A", "TXN-AML-0118B", "TXN-AML-0118C"],
    currency: "MAD",
    first_detected_at: "2026-11-02 15:10:00",
    event_min: "2026-11-02 15:05:30",
    event_max: "2026-11-02 15:09:12",
    total_amount: 95000.00,
    evidence: {
      accounts: ["ACC-0055", "ACC-0062", "ACC-0071"],
      edges: [
        { transaction_id: "TXN-AML-0118A", src: "ACC-0055", dst: "ACC-0062", amount: 33000.00, currency: "MAD", time: "2026-11-02T15:05:30Z" },
        { transaction_id: "TXN-AML-0118B", src: "ACC-0062", dst: "ACC-0071", amount: 31500.00, currency: "MAD", time: "2026-11-02T15:07:45Z" },
        { transaction_id: "TXN-AML-0118C", src: "ACC-0071", dst: "ACC-0055", amount: 30500.00, currency: "MAD", time: "2026-11-02T15:09:12Z" },
      ],
      matching_window: { start: "2026-11-02T15:05:00Z", end: "2026-11-02T15:15:00Z" }
    }
  }
];

export async function getAlerts(): Promise<FraudAlert[]> {
  return MOCK_ALERTS;
}

export async function getAlertById(alertId: string): Promise<FraudAlert | null> {
  const alert = MOCK_ALERTS.find((a) => a.alert_id === alertId);
  return alert || null;
}

export async function getAccountMetrics(): Promise<AccountMetric[]> {
  return [
    { account_id: "ACC-MERCHANT-HUB", pagerank: 0.1428, component_id: 1, alert_count: 0, total_volume: 1250000.0, is_hub: true },
    { account_id: "ACC-UTILITY-BILLING", pagerank: 0.1105, component_id: 1, alert_count: 0, total_volume: 980000.0, is_hub: true },
    { account_id: "ACC-0105", pagerank: 0.0512, component_id: 4, alert_count: 1, total_volume: 420000.0, is_hub: false },
    { account_id: "ACC-0081", pagerank: 0.0482, component_id: 2, alert_count: 2, total_volume: 320000.0, is_hub: false },
    { account_id: "ACC-0014", pagerank: 0.0451, component_id: 2, alert_count: 1, total_volume: 308000.0, is_hub: false },
    { account_id: "ACC-0003", pagerank: 0.0439, component_id: 2, alert_count: 1, total_volume: 295000.0, is_hub: false },
    { account_id: "ACC-0312", pagerank: 0.0395, component_id: 4, alert_count: 1, total_volume: 215000.0, is_hub: false },
    { account_id: "ACC-0789", pagerank: 0.0381, component_id: 4, alert_count: 1, total_volume: 205000.0, is_hub: false },
    { account_id: "ACC-0012", pagerank: 0.0215, component_id: 3, alert_count: 1, total_volume: 98000.0, is_hub: false },
    { account_id: "ACC-0045", pagerank: 0.0201, component_id: 3, alert_count: 1, total_volume: 92000.0, is_hub: false },
    { account_id: "ACC-0089", pagerank: 0.0198, component_id: 3, alert_count: 1, total_volume: 89000.0, is_hub: false },
    { account_id: "ACC-0055", pagerank: 0.0185, component_id: 5, alert_count: 1, total_volume: 64500.0, is_hub: false },
    { account_id: "ACC-0062", pagerank: 0.0179, component_id: 5, alert_count: 1, total_volume: 63000.0, is_hub: false },
    { account_id: "ACC-0071", pagerank: 0.0172, component_id: 5, alert_count: 1, total_volume: 61000.0, is_hub: false },
    { account_id: "ACC-0021", pagerank: 0.0120, component_id: 6, alert_count: 1, total_volume: 14200.0, is_hub: false },
  ];
}

export async function getPipelineHealth(): Promise<PipelineHealth> {
  return {
    status: "HEALTHY",
    last_batch_time: new Date().toISOString(),
    high_water_mark: new Date(Date.now() - 120000).toISOString(),
    transactions_ingested: 117805,
    active_alerts: MOCK_ALERTS.length,
    tables: {
      bronze_transactions: 117805,
      silver_transactions: 117760,
      quarantined_transactions: 45,
      fraud_alerts: MOCK_ALERTS.length,
      account_graph_metrics: 20000,
    }
  };
}
