import { useState } from 'react';
import type { SceneMetadata } from '../../types';

interface SceneTimelineProps {
  scenes: SceneMetadata[];
  selectedIndex: number;
  onSelect: (index: number) => void;
  onReorder: (fromIndex: number, toIndex: number) => void;
}

export default function SceneTimeline({ scenes, selectedIndex, onSelect, onReorder }: SceneTimelineProps) {
  const [dragIndex, setDragIndex] = useState<number | null>(null);
  const [dropIndex, setDropIndex] = useState<number | null>(null);

  const handleDragStart = (e: React.DragEvent, index: number) => {
    setDragIndex(index);
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', String(index));
  };

  const handleDragOver = (e: React.DragEvent, index: number) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    setDropIndex(index);
  };

  const handleDragLeave = () => {
    setDropIndex(null);
  };

  const handleDrop = (e: React.DragEvent, toIndex: number) => {
    e.preventDefault();
    const fromIndex = dragIndex;
    setDragIndex(null);
    setDropIndex(null);
    if (fromIndex !== null && fromIndex !== toIndex) {
      onReorder(fromIndex, toIndex);
    }
  };

  const handleDragEnd = () => {
    setDragIndex(null);
    setDropIndex(null);
  };

  return (
    <div className="w-full overflow-x-auto">
      <div className="flex gap-3 p-4 min-w-max">
        {scenes.map((scene, index) => (
          <div
            key={scene.scene_number}
            draggable
            onDragStart={(e) => handleDragStart(e, index)}
            onDragOver={(e) => handleDragOver(e, index)}
            onDragLeave={handleDragLeave}
            onDrop={(e) => handleDrop(e, index)}
            onDragEnd={handleDragEnd}
            onClick={() => onSelect(index)}
            className={`flex-shrink-0 w-36 cursor-pointer rounded-lg overflow-hidden border-2 transition-all ${
              index === selectedIndex
                ? 'border-primary-600 shadow-lg shadow-primary-600/20'
                : 'border-gray-700 hover:border-gray-600'
            } ${dropIndex === index ? 'scale-105 border-blue-400' : ''} ${
              dragIndex === index ? 'opacity-50' : ''
            }`}
          >
            <div className="h-20 bg-gray-700 relative">
              {scene.thumbnail_url ? (
                <img
                  src={scene.thumbnail_url}
                  alt={`Scene ${scene.scene_number}`}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-700 to-gray-800">
                  <span className="text-gray-500 text-xs">No thumbnail</span>
                </div>
              )}
              <span className="absolute top-1 left-1 bg-black/70 text-white text-xs px-1.5 py-0.5 rounded">
                {scene.scene_number}
              </span>
            </div>
            <div className="p-2 bg-gray-800">
              <p className="text-xs text-gray-400 truncate">{scene.narration?.slice(0, 30) || 'Scene'}</p>
              <p className="text-xs text-gray-500 mt-0.5">{scene.duration_seconds.toFixed(1)}s</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
