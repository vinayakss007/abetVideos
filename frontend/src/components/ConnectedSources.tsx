import { useEffect, useState } from 'react';
import { Plug, CheckCircle, XCircle } from 'lucide-react';
import { getProviders } from '../api/client';
import type { MediaProviderStatus } from '../types';

export default function ConnectedSources() {
  const [providers, setProviders] = useState<MediaProviderStatus[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getProviders()
      .then(setProviders)
      .catch(() => setProviders([]))
      .finally(() => setLoading(false));
  }, []);

  const activeCount = providers.filter((p) => p.configured).length;

  if (loading) {
    return null;
  }

  return (
    <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-800/50 border border-gray-700 rounded-lg text-xs">
      <Plug className="w-3.5 h-3.5 text-gray-400" />
      <span className="text-gray-400">Sources:</span>
      <span className="text-primary-400 font-medium">{activeCount}/{providers.length}</span>
      <div className="hidden sm:flex items-center gap-1.5 ml-1 border-l border-gray-700 pl-2">
        {providers.map((p) => (
          <div
            key={p.name}
            className="flex items-center gap-0.5"
            title={`${p.name}: ${p.configured ? 'connected' : 'not configured'}`}
          >
            {p.configured ? (
              <CheckCircle className="w-3 h-3 text-green-400" />
            ) : (
              <XCircle className="w-3 h-3 text-gray-600" />
            )}
            <span className={p.configured ? 'text-gray-300' : 'text-gray-600'}>
              {p.name}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
