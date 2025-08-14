"use client";
import { useState } from "react";
import { postForm } from "../lib/fetcher";

export default function Upload({ onRun }: { onRun: (id: string) => void }) {
  const [files, setFiles] = useState<FileList | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    const fd = new FormData();
    fd.append("recipe_path", "recipes/beverage.json");
    if (files) Array.from(files).forEach(f => fd.append("files", f));
    const { run_id } = await postForm("/generate", fd);
    onRun(run_id);
    setLoading(false);
  };

  return (
    <form onSubmit={submit} className="card grid" style={{ maxWidth: 640 }}>
      <h2>Generate Campaign</h2>
      <label>Upload logo / moodboard (optional)
        <input type="file" multiple onChange={e => setFiles(e.target.files)} />
      </label>
      <button disabled={loading}>{loading ? "Generating…" : "Generate"}</button>
    </form>
  );
}
