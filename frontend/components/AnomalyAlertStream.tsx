"use client";

import { useEffect, useState } from "react";
import type { AnomalyAlert } from "../lib/types";

interface Props {
  apiBaseUrl: string;
}

export function AnomalyAlertStream({ apiBaseUrl }: Props) {
  const [anomalies, setAnomalies] = useState<AnomalyAlert[]>([]);
  const [loading, setLoading] = useState(false);

  async function triggerDetection() {
    setLoading(true);
    try {
      const res = await fetch(`${apiBaseUrl}/anomalies/detect`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ window_minutes: 60 }),
      });

      if (res.ok) {
        const data = await res.json();
        setAnomalies(data.anomalies || []);
      }
    } catch {
      // Stream fallback
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    triggerDetection();
    const interval = setInterval(triggerDetection, 15000);
    return () => clearInterval(interval);
  }, [apiBaseUrl]);

  return (
    <div className="anomaly-stream-card">
      <div className="stream-header">
        <div>
          <h3>Real-Time Anomaly Stream</h3>
          <p>Continuous monitoring for corridor breaches, speed spikes, & stale heartbeats.</p>
        </div>
        <button className="scan-btn" onClick={triggerDetection} disabled={loading}>
          {loading ? "Scanning..." : "Trigger Scan"}
        </button>
      </div>

      <div className="alerts-list">
        {anomalies.length === 0 ? (
          <div className="empty-alerts">
            <span className="clean-badge">All Telemetry Signals Nominal</span>
            <p>No operational anomalies or corridor deviations detected in active 60m window.</p>
          </div>
        ) : (
          anomalies.map((alert) => (
            <div key={alert.anomaly_id} className={`alert-item alert-${alert.anomaly_type}`}>
              <div className="alert-top">
                <span className="anomaly-type-pill">{alert.anomaly_type.replace("_", " ").toUpperCase()}</span>
                <span className="anomaly-score">Score: {alert.anomaly_score}</span>
              </div>
              <p className="alert-reason">{alert.reason}</p>
              <div className="alert-footer">
                <span>Entity: <strong>{alert.external_id || alert.entity_id.substring(0, 8)}</strong></span>
                <span>{new Date(alert.detected_at).toLocaleTimeString()}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
