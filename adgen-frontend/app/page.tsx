// app/page.tsx - Main "New Ad Run" form
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import RunForm from '@/components/RunForm';
import { createRun } from '@/lib/api';
import Toast from '@/components/Toast';

export default function HomePage() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const router = useRouter();

  const handleSubmit = async (data: {
    prompt: string;
    negative_prompt?: string;
    seed?: number;
    logo_image?: string;
    mood_image?: string;
  }) => {
    setIsSubmitting(true);
    try {
      const result = await createRun(data);
      setToast({ message: 'Run created successfully!', type: 'success' });
      router.push(`/runs/${result.run_id}`);
    } catch (error) {
      setToast({ message: 'Failed to create run', type: 'error' });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">AdGen Studio</h1>
          <p className="text-lg text-gray-600">Create AI-powered advertisements</p>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-8">
          <h2 className="text-2xl font-semibold mb-6">New Advertisement Run</h2>
          <RunForm onSubmit={handleSubmit} isSubmitting={isSubmitting} />
        </div>
      </div>

      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
}
