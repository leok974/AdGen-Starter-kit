// lib/api.ts - API utilities
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export interface CreateRunRequest {
  prompt: string;
  negative_prompt?: string;
  seed?: number;
  logo_image?: string;
  mood_image?: string;
}

export interface CreateRunResponse {
  run_id: string;
  status: string;
  prompt_id?: string;
}

export async function createRun(data: CreateRunRequest): Promise<CreateRunResponse> {
  const response = await fetch(`${API_BASE}/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to create run: ${error}`);
  }

  return response.json();
}

export async function getRuns() {
  const response = await fetch(`${API_BASE}/runs`);

  if (!response.ok) {
    throw new Error('Failed to fetch runs');
  }

  return response.json();
}

export async function getRun(runId: string) {
  const response = await fetch(`${API_BASE}/runs/${runId}`);

  if (!response.ok) {
    throw new Error('Failed to fetch run details');
  }

  return response.json();
}

export async function cancelRun(runId: string) {
  const response = await fetch(`${API_BASE}/runs/${runId}/cancel`, {
    method: 'POST',
  });

  if (!response.ok) {
    throw new Error('Failed to cancel run');
  }

  return response.json();
}
