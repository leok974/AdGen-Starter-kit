import Link from 'next/link';
import StatusPill from './StatusPill';
import { Run } from '@/types';

interface RunTableProps {
  runs: Run[];
  loading: boolean;
}

export default function RunTable({ runs, loading }: RunTableProps) {
  if (loading) {
    return (
      <div className="p-8 text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Loading runs...</p>
      </div>
    );
  }

  if (runs.length === 0) {
    return (
      <div className="p-8 text-center text-gray-500">
        No runs found. <Link href="/" className="text-blue-600 hover:underline">Create your first run</Link>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Run ID
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Prompt
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Status
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Created
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Duration
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {runs.map((run) => (
            <tr key={run.run_id} className="hover:bg-gray-50">
              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                <Link
                  href={`/runs/${run.run_id}`}
                  className="text-blue-600 hover:underline"
                >
                  {run.run_id.slice(0, 8)}...
                </Link>
              </td>
              <td className="px-6 py-4 text-sm text-gray-900 max-w-xs truncate">
                {run.prompt}
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <StatusPill status={run.status} />
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {new Date(run.created_at).toLocaleDateString()}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {run.duration ? `${run.duration}s` : '-'}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm">
                <Link
                  href={`/runs/${run.run_id}`}
                  className="text-blue-600 hover:underline"
                >
                  View Details
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
