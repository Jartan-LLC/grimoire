// The records the logkit modules pass to one another.

// Severity levels, least severe first.
export const LEVELS = ["debug", "info", "notice", "warning", "error", "critical"] as const;

export type Level = (typeof LEVELS)[number];

// One log line, whatever format it came from.
export interface LogRecord {
  // Milliseconds since the Unix epoch, UTC.
  at: number;
  source: string;
  level: Level;
  message: string;
  // Everything the line carried that has no field of its own, as strings.
  fields: Record<string, string>;
  status?: number;
  latencyMs?: number;
  bytes?: number;
  // The request path without its query string.
  path?: string;
}

// A line a parser could not read; `line` counts from 1.
export interface LineError {
  line: number;
  message: string;
}

export interface IngestResult {
  records: LogRecord[];
  errors: LineError[];
}

export type StatusClass = "1xx" | "2xx" | "3xx" | "4xx" | "5xx" | "other";

export interface PathCount {
  path: string;
  count: number;
}

// One tumbling window of records. A percentile is null when no record in the window
// carried a latency.
export interface WindowStats {
  start: number;
  end: number;
  count: number;
  errors: number;
  // errors / count, from 0 to 1; 0 for an empty window.
  errorRate: number;
  p50: number | null;
  p95: number | null;
  p99: number | null;
  bytes: number;
  statusClasses: Record<StatusClass, number>;
  topPaths: PathCount[];
}

export type AlertState = "inactive" | "pending" | "firing" | "resolved";

// A change of an alert rule's state at the end of a window.
export interface AlertEvent {
  rule: string;
  // The rule's metric as written, such as "error_rate" or "p95(latency)".
  metric: string;
  state: AlertState;
  at: number;
  // The metric's value in that window; null when the window had no data for it.
  value: number | null;
}
