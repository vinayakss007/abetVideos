import { useEffect, useState } from 'react';

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
    <div className="px-3 py-2">
      <div className="flex items-center justify-between text-xs mb-2">
        <span className="text-gray-500">Sources</span>
        <span className="text-primary-400 font-medium">
          {activeCount}/{providers.length} active
        </span>
      </div>
      <div className="flex flex-wrap gap-1">
        {providers.map((p) => (
          <span
            key={p.name}
            className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium ${
              p.configured
                ? 'bg-green-900/30 text-green-400 border border-green-800/40'
                : 'bg-gray-800 text-gray-600 border border-gray-700'
            }`}
            title={`${p.name}: ${p.configured ? 'connected' : 'not configured'}`}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${
              p.configured ? 'bg-green-400' : 'bg-gray-600'
            }`} />
            {p.name}
          </span>
        ))}
      </div>
    </div>
  );
}
