'use client';

import { useState } from 'react';

interface RunFormProps {
  onSubmit: (data: {
    prompt: string;
    negative_prompt?: string;
    seed?: number;
    logo_image?: string;
    mood_image?: string;
  }) => void;
  isSubmitting: boolean;
}

export default function RunForm({ onSubmit, isSubmitting }: RunFormProps) {
  const [formData, setFormData] = useState({
    prompt: '',
    negative_prompt: '',
    seed: '',
    logo_image: '',
    mood_image: ''
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      prompt: formData.prompt,
      negative_prompt: formData.negative_prompt || undefined,
      seed: formData.seed ? parseInt(formData.seed) : undefined,
      logo_image: formData.logo_image || undefined,
      mood_image: formData.mood_image || undefined,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Advertisement Prompt *
        </label>
        <textarea
          value={formData.prompt}
          onChange={(e) => setFormData({ ...formData, prompt: e.target.value })}
          placeholder="Describe the advertisement you want to create..."
          rows={4}
          required
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Negative Prompt (Optional)
        </label>
        <textarea
          value={formData.negative_prompt}
          onChange={(e) => setFormData({ ...formData, negative_prompt: e.target.value })}
          placeholder="What you don't want in the advertisement..."
          rows={2}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Seed (Optional)
          </label>
          <input
            type="number"
            value={formData.seed}
            onChange={(e) => setFormData({ ...formData, seed: e.target.value })}
            placeholder="Random seed"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Logo Image URL (Optional)
          </label>
          <input
            type="url"
            value={formData.logo_image}
            onChange={(e) => setFormData({ ...formData, logo_image: e.target.value })}
            placeholder="https://..."
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Mood Image URL (Optional)
          </label>
          <input
            type="url"
            value={formData.mood_image}
            onChange={(e) => setFormData({ ...formData, mood_image: e.target.value })}
            placeholder="https://..."
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div className="flex justify-end">
        <button
          type="submit"
          disabled={!formData.prompt.trim() || isSubmitting}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {isSubmitting ? 'Creating Run...' : 'Create Advertisement'}
        </button>
      </div>
    </form>
  );
}
