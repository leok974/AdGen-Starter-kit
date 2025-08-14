"use client";
import { useState } from "react";
import Upload from "./components/Upload";
import Gallery from "./components/Gallery";

export default function Page() {
  const [runId, setRunId] = useState("");
  return (
    <main className="grid" style={{ placeItems: "start center", padding: 24 }}>
      <h1>AdGen — Weekend Prototype</h1>
      <Upload onRun={setRunId} />
      <Gallery runId={runId} />
    </main>
  );
}
