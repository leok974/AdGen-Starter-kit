"use client";
import { useEffect, useState } from "react";
import { getJSON, API_BASE } from "../lib/fetcher";

export default function Gallery({ runId }: { runId: string }) {
  const [data, setData] = useState<any | null>(null);
  useEffect(() => {
    if (!runId) return;
    const t = setInterval(async () => {
      const d = await getJSON(`/runs/${runId}`);
      setData(d);
    }, 1000);
    return () => clearInterval(t);
  }, [runId]);

  if (!runId) return null;
  if (!data) return <div className="card">Waiting for results…</div>;

  return (
    <div className="card grid">
      <h3>Run: {runId}</h3>
      <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))" }}>
        {data.thumbnails?.map((t: string) => (
          <img key={t} src={`${API_BASE}/runs/${runId}/${t}`} alt={t} style={{ width: "100%", borderRadius: 12 }} />
        ))}
      </div>
      <a href={`${API_BASE}/runs/${runId}`} target="_blank">View JSON</a>
    </div>
  );
}
