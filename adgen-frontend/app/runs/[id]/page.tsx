'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import AssetGrid from '@/components/AssetGrid';
import StatusPill from '@/components/StatusPill';
import { getRun, cancelRun } from '@/lib/api';
import { RunDetail } from '@/types';

export default function RunDetailPage() {
  const params = useParams();
  const runId = params.id as string;
  const [run, setRun] = useState<RunDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [isFinalizingRun, setIsFinalizingRun] = useState(false);

  useEffect(() => {
    if (runId) {
      loadRun();
      const interval = setInterval(loadRun, 3000); // Poll every 3 seconds
      return () => clearInterval(interval);
    }
  }, [runId]);

  const loadRun = async () => {
    try {
      const data = await getRun(runId);
      setRun(data);
      
      // Auto-finalize if status is RUNNING and we haven't finalized yet
      if (data.status === 'RUNNING' && !data.finished_at && !isFinalizingRun) {
        setIsFinalizingRun(true);
        try {
          console.log('Auto-finalizing run:', runId);
          const finalizeResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/finalize/${runId}`, {
            method: 'POST'
          });
          
          if (finalizeResponse.ok) {
            const finalizedData = await finalizeResponse.json();
            setRun(finalizedData);
          } else {
            console.error('Finalize request failed:', finalizeResponse.status);
          }
        } catch (finalizeError) {
          console.error('Auto-finalize failed:', finalizeError);
        } finally {
          setIsFinalizingRun(false);
        }
      }
    } catch (error) {
      console.error('Failed to load run:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async () => {
    if (run && (run.status === 'PENDING' || run.status === 'RUNNING')) {
      try {
        await cancelRun(runId);
        await loadRun();
      } catch (error) {
        console.error('Failed to cancel run:', error);
      }
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading run details...</p>
        </div>
      </div>
    );
  }

  if (!run) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600">Run not found</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Run {runId}</h1>
              <div className="flex items-center space-x-4 mt-2">
                <StatusPill status={run.status} />
                <span className="text-sm text-gray-600">
                  Created: {new Date(run.created_at).toLocaleString()}
                </span>
                {run.finished_at && (
                  <span className="text-sm text-gray-600">
                    Finished: {new Date(run.finished_at).toLocaleString()}
                  </span>
                )}
                {isFinalizingRun && (
                  <span className="text-sm text-blue-600 font-medium">
                    Finalizing...
                  </span>
                )}
              </div>
            </div>

            {(run.status === 'PENDING' || run.status === 'RUNNING') && !isFinalizingRun && (
              <button
                onClick={handleCancel}
                className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700"
              >
                Cancel Run
              </button>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Run Details */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-lg font-semibold mb-4">Run Details</h2>
              <dl className="space-y-3">
                <div>
                  <dt className="text-sm font-medium text-gray-500">Prompt</dt>
                  <dd className="text-sm text-gray-900">{run.inputs.prompt}</dd>
                </div>
                {run.inputs.negative_prompt && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Negative Prompt</dt>
                    <dd className="text-sm text-gray-900">{run.inputs.negative_prompt}</dd>
                  </div>
                )}
                {run.inputs.seed && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Seed</dt>
                    <dd className="text-sm text-gray-900">{run.inputs.seed}</dd>
                  </div>
                )}
                <div>
                  <dt className="text-sm font-medium text-gray-500">Duration</dt>
                  <dd className="text-sm text-gray-900">
                    {run.finished_at
                      ? `${Math.round((new Date(run.finished_at).getTime() - new Date(run.created_at).getTime()) / 1000)}s`
                      : 'In progress...'
                    }
                  </dd>
                </div>
              </dl>
            </div>
          </div>

          {/* Assets */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-lg font-semibold mb-4">Generated Assets</h2>
              {run.artifacts && run.artifacts.length > 0 ? (
                <AssetGrid artifacts={run.artifacts} runId={runId} />
              ) : (
                <div className="text-center py-12 text-gray-500">
                  {run.status === 'COMPLETED' ? 'No assets generated' : 'Assets will appear here when generation completes'}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}