// types/index.ts - TypeScript types
export interface Run {
  run_id: string;
  prompt: string;
  status: string;
  created_at: string;
  finished_at?: string;
  duration?: number;
}

export interface RunDetail {
  run_id: string;
  status: string;
  created_at: string;
  finished_at?: string;
  inputs: {
    prompt: string;
    negative_prompt?: string;
    seed?: number;
    logo_image?: string;
    mood_image?: string;
  };
  artifacts?: Array<{
    type: string;
    url: string;
    filename?: string;
    size?: number;
  }>;
  logs_url?: string;
}
