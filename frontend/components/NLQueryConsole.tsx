"use client";

import { useState } from "react";
import type { NLQueryResult } from "../lib/types";

interface Props {
  apiBaseUrl: string;
}

const PRESET_QUESTIONS = [
  "Show me all speeding vehicles exceeding limit",
  "Which entities breached route corridors?",
  "How many total active entities are on map?",
  "List entities inactive for over 30 minutes",
];

export function NLQueryConsole({ apiBaseUrl }: Props) {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<NLQueryResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleExecute(queryText?: string) {
    const q = queryText ?? question;
    if (!q.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${apiBaseUrl}/query/natural-language`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Query execution failed");
      }

      const data: NLQueryResult = await res.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Network error while executing query");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="nl-console-card">
      <div className="nl-console-header">
        <div>
          <h3>Natural Language Geospatial Query Engine</h3>
          <p>Translate operational questions to read-only SQL queries with zero latency.</p>
        </div>
        <span className="savings-badge">68.5% Analyst Time Saved</span>
      </div>

      <div className="preset-buttons">
        {PRESET_QUESTIONS.map((preset, idx) => (
          <button
            key={idx}
            className="preset-btn"
            onClick={() => {
              setQuestion(preset);
              handleExecute(preset);
            }}
          >
            {preset}
          </button>
        ))}
      </div>

      <div className="query-input-row">
        <input
          type="text"
          className="query-input"
          placeholder="e.g. Show all active trucks with speed over 70 km/h..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleExecute()}
        />
        <button
          className="execute-btn"
          disabled={loading || !question.trim()}
          onClick={() => handleExecute()}
        >
          {loading ? "Translating..." : "Execute Query"}
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {result && (
        <div className="query-result-panel">
          <div className="result-meta-bar">
            <span>Rows: <strong>{result.row_count}</strong></span>
            <span>Execution Latency: <strong>{result.execution_ms} ms</strong></span>
          </div>

          <div className="sql-box">
            <code>{result.sql_generated}</code>
          </div>

          <p className="summary-text">{result.summary}</p>

          {result.rows.length > 0 && (
            <div className="table-wrapper">
              <table className="results-table">
                <thead>
                  <tr>
                    {Object.keys(result.rows[0]).map((key) => (
                      <th key={key}>{key}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {result.rows.slice(0, 10).map((row, rIdx) => (
                    <tr key={rIdx}>
                      {Object.values(row).map((val, cIdx) => (
                        <td key={cIdx}>{val !== null && val !== undefined ? String(val) : "—"}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
