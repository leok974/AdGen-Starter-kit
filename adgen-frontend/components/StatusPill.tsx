interface StatusPillProps {
  status: string;
}

export default function StatusPill({ status }: StatusPillProps) {
  const getStatusStyles = (status: string) => {
    switch (status.toUpperCase()) {
      case 'PENDING':
        return 'bg-gray-100 text-gray-800';
      case 'RUNNING':
      case 'GENERATING':
        return 'bg-blue-100 text-blue-800';
      case 'COMPLETED':
      case 'SUCCEEDED':
        return 'bg-green-100 text-green-800';
      case 'FAILED':
      case 'ERROR':
        return 'bg-red-100 text-red-800';
      case 'CANCELLED':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusStyles(status)}`}>
      {status.toUpperCase()}
    </span>
  );
}
