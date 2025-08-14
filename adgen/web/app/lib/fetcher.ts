export const API = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
// Backward-compat in case some files still import API_BASE
export const API_BASE = API;

export async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API}${path}`, { cache: 'no-store' });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function postJSON<T>(path: string, body: any): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function postForm<T>(path: string, form: FormData): Promise<T> {
  const res = await fetch(`${API}${path}`, { method: 'POST', body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
