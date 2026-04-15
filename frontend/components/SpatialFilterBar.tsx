"use client";

import { useState } from "react";

interface Props {
  apiBaseUrl: string;
  onFilterResults: (entities: any[]) => void;
}

export function SpatialFilterBar({ apiBaseUrl, onFilterResults }: Props) {
  const [lat, setLat] = useState("37.7749");
  const [lon, setLon] = useState("-122.4194");
  const [radiusKm, setRadiusKm] = useState("25.0");
  const [loading, setLoading] = useState(false);

  async function handleRadiusSearch() {
    setLoading(true);
    try {
      const res = await fetch(
        `${apiBaseUrl}/entities/spatial/radius?lat=${lat}&lon=${lon}&radius_km=${radiusKm}`
      );
      if (res.ok) {
        const data = await res.json();
        onFilterResults(data.entities || []);
      }
    } catch {
      // Ignore network errors
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="spatial-filter-bar">
      <div className="filter-title">
        <h4>Geospatial Proximity Search</h4>
        <span>Filter fleet by geographic radius</span>
      </div>

      <div className="filter-inputs">
        <div className="input-group">
          <label>Lat</label>
          <input value={lat} onChange={(e) => setLat(e.target.value)} type="number" step="0.0001" />
        </div>
        <div className="input-group">
          <label>Lon</label>
          <input value={lon} onChange={(e) => setLon(e.target.value)} type="number" step="0.0001" />
        </div>
        <div className="input-group">
          <label>Radius (km)</label>
          <input value={radiusKm} onChange={(e) => setRadiusKm(e.target.value)} type="number" step="0.5" />
        </div>
        <button className="filter-btn" onClick={handleRadiusSearch} disabled={loading}>
          {loading ? "Searching..." : "Apply Spatial Filter"}
        </button>
      </div>
    </div>
  );
}
