"use client";

import { LiveMap } from "../components/live-map";
import { NLQueryConsole } from "../components/NLQueryConsole";
import { AnomalyAlertStream } from "../components/AnomalyAlertStream";

export default function HomePage() {
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

  return (
    <main className="page-shell">
      <header className="hero">
        <div className="hero-branding">
          <div className="hero-badge">OPERATIONS COMMAND CENTER</div>
          <h1>Meridian: Real-Time Geospatial Intelligence System</h1>
          <p>
            Sub-second telemetry ingestion (24,272 msgs/sec), autonomous corridor deviation scoring,
            and zero-latency natural language geospatial querying.
          </p>
        </div>
        <div className="hero-metrics">
          <div className="metric-box">
            <span className="m-val">24.2k</span>
            <span className="m-lbl">Ingest msgs/sec</span>
          </div>
          <div className="metric-box">
            <span className="m-val">&lt; 8ms</span>
            <span className="m-lbl">NL Translation</span>
          </div>
          <div className="metric-box">
            <span className="m-val">68.5%</span>
            <span className="m-lbl">Analyst Efficiency</span>
          </div>
        </div>
      </header>

      <div className="dashboard-grid">
        <div className="main-column">
          <section className="map-section">
            <LiveMap />
          </section>

          <section className="query-section">
            <NLQueryConsole apiBaseUrl={apiBaseUrl} />
          </section>
        </div>

        <div className="side-column">
          <section className="anomaly-section">
            <AnomalyAlertStream apiBaseUrl={apiBaseUrl} />
          </section>
        </div>
      </div>
    </main>
  );
}
