import { useState } from 'react';
import { Download, Eye } from 'lucide-react';

interface Artifact {
  type: string;
  url: string;
  filename?: string;
  size?: number;
}

interface AssetGridProps {
  artifacts: Artifact[];
}

export default function AssetGrid({ artifacts }: AssetGridProps) {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);

  const downloadAsset = (url: string, filename?: string) => {
    const link = document.createElement('a');
    link.href = url;
    link.download = filename || 'asset';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const isImage = (type: string) => type.startsWith('image/') || type === 'image';
  const isVideo = (type: string) => type.startsWith('video/') || type === 'video';

  return (
    <>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {artifacts.map((artifact, index) => (
          <div key={index} className="border rounded-lg overflow-hidden">
            {isImage(artifact.type) && (
              <div className="relative group">
                <img
                  src={artifact.url}
                  alt={`Generated asset ${index + 1}`}
                  className="w-full h-48 object-cover cursor-pointer"
                  onClick={() => setSelectedImage(artifact.url)}
                />
                <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-all duration-200 flex items-center justify-center">
                  <button
                    onClick={() => setSelectedImage(artifact.url)}
                    className="opacity-0 group-hover:opacity-100 bg-white text-gray-800 p-2 rounded-full shadow-lg transition-opacity duration-200"
                  >
                    <Eye className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}

            {isVideo(artifact.type) && (
              <video
                controls
                className="w-full h-48 object-cover"
                src={artifact.url}
              />
            )}

            <div className="p-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {artifact.filename || `Asset ${index + 1}`}
                  </p>
                  <p className="text-xs text-gray-500">{artifact.type}</p>
                  {artifact.size && (
                    <p className="text-xs text-gray-500">
                      {(artifact.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  )}
                </div>
                <button
                  onClick={() => downloadAsset(artifact.url, artifact.filename)}
                  className="p-2 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded"
                >
                  <Download className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Image Modal */}
      {selectedImage && (
        <div
          className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4"
          onClick={() => setSelectedImage(null)}
        >
          <div className="max-w-4xl max-h-full">
            <img
              src={selectedImage}
              alt="Full size preview"
              className="max-w-full max-h-full object-contain"
            />
          </div>
        </div>
      )}
    </>
  );
}
