// app/runs/page.tsx - Runs list page
'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import RunTable from '@/components/RunTable';
import StatusPill from '@/components/StatusPill';
import { getRuns } from '@/lib/api';
import { Run } from '@/types';

export default function RunsPage() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    loadRuns();
    const interval = setInterval(loadRuns, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const loadRuns = async () => {
    try {
      const data = await getRuns();
      setRuns(data);
    } catch (error) {
      console.error('Failed to load runs:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredRuns = runs.filter(run =>
    filter === 'all' || run.status.toLowerCase() === filter
  );

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Advertisement Runs</h1>
          <Link
            href="/"
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            New Run
          </Link>
        </div>

        <div className="bg-white rounded-lg shadow-sm">
          <div className="p-6 border-b">
            <div className="flex items-center space-x-4">
              <span className="text-sm font-medium text-gray-700">Filter:</span>
              {['all', 'pending', 'running', 'completed', 'failed'].map(status => (
                <button
                  key={status}
                  onClick={() => setFilter(status)}
                  className={`px-3 py-1 text-sm rounded-full ${
                    filter === status
                      ? 'bg-blue-100 text-blue-800'
                      : 'text-gray-600 hover:text-gray-800'
                  }`}
                >
                  {status.charAt(0).toUpperCase() + status.slice(1)}
                </button>
              ))}
            </div>
          </div>

          <RunTable runs={filteredRuns} loading={loading} />
        </div>
      </div>
    </div>
  );
}
