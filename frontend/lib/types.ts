export type LiveEntity = {
  entity_id: string;
  external_id: string;
  type: string;
  status: string;
  last_seen_at: string;
  latitude: number;
  longitude: number;
  speed: number | null;
  heading: number | null;
};

export type PositionUpdateMessage = {
  type: "position_update";
  event_id: string;
  entity_id: string;
  external_id: string;
  status: string;
  event_time: string;
  latitude: number;
  longitude: number;
  speed: number | null;
  heading: number | null;
};

export type AnomalyAlert = {
  anomaly_id: string;
  entity_id: string;
  external_id?: string;
  anomaly_type: "route_deviation" | "speed_spike" | "heading_flip" | "stale_signal" | string;
  anomaly_score: number;
  reason: string;
  detected_at: string;
};

export type NLQueryResult = {
  question: string;
  sql_generated: string;
  execution_ms: number;
  summary: string;
  row_count: number;
  rows: Record<string, any>[];
};
