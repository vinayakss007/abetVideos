import { Plus, X } from 'lucide-react';
import type { TextOverlayInstruction, SceneMetadata } from '../../types';

interface TextOverlayEditorProps {
  scene: SceneMetadata;
  sceneNumber: number;
  overlays: TextOverlayInstruction[];
  onAdd: (overlay: TextOverlayInstruction) => void;
  onRemove: (index: number) => void;
  onUpdate: (index: number, overlay: TextOverlayInstruction) => void;
}

const COLORS = ['#ffffff', '#000000', '#ef4444', '#3b82f6', '#22c55e', '#eab308', '#f97316', '#a855f7'];
const FONT_SIZES = [16, 20, 24, 32, 48, 64];

export default function TextOverlayEditor({ scene, sceneNumber, overlays, onAdd, onRemove, onUpdate }: TextOverlayEditorProps) {
  const sceneOverlays = overlays.filter((o) => o.scene_number === sceneNumber);

  const handleAdd = () => {
    onAdd({
      text: 'New Text',
      x: 50,
      y: 50,
      font_size: 24,
      color: '#ffffff',
      scene_number: sceneNumber,
    });
  };

  const getOverlayGlobalIndex = (localIndex: number): number => {
    let count = 0;
    for (let i = 0; i < overlays.length; i++) {
      if (overlays[i].scene_number === sceneNumber) {
        if (count === localIndex) return i;
        count++;
      }
    }
    return -1;
  };

  return (
    <div className="space-y-4 p-4 bg-gray-800 rounded-lg border border-gray-700">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium text-gray-200">Text Overlays</h4>
        <button
          type="button"
          onClick={handleAdd}
          className="flex items-center gap-1 px-2 py-1 text-xs bg-primary-600 hover:bg-primary-500 text-white rounded transition-colors"
        >
          <Plus className="w-3 h-3" />
          Add Overlay
        </button>
      </div>

      {/* DOM-based preview */}
      <div className="relative w-full aspect-video bg-gray-900 rounded overflow-hidden border border-gray-700">
        {scene.thumbnail_url ? (
          <img src={scene.thumbnail_url} alt="Scene preview" className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full bg-gradient-to-br from-gray-700 to-gray-900" />
        )}
        {sceneOverlays.map((overlay, i) => (
          <span
            key={i}
            className="absolute pointer-events-none"
            style={{
              left: `${overlay.x}%`,
              top: `${overlay.y}%`,
              transform: 'translate(-50%, -50%)',
              fontSize: `${overlay.font_size * 0.3}px`,
              color: overlay.color,
              fontWeight: 'bold',
              textShadow: '1px 1px 2px rgba(0,0,0,0.8)',
            }}
          >
            {overlay.text}
          </span>
        ))}
      </div>

      {/* Overlay controls */}
      <div className="space-y-3 max-h-60 overflow-y-auto">
        {sceneOverlays.map((overlay, localIndex) => {
          const globalIndex = getOverlayGlobalIndex(localIndex);
          return (
            <div key={localIndex} className="p-3 bg-gray-900 rounded border border-gray-700 space-y-2">
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={overlay.text}
                  onChange={(e) => onUpdate(globalIndex, { ...overlay, text: e.target.value })}
                  className="flex-1 px-2 py-1 text-sm bg-gray-800 border border-gray-600 rounded text-gray-200"
                  placeholder="Enter text"
                />
                <button
                  type="button"
                  onClick={() => onRemove(globalIndex)}
                  className="p-1 text-gray-400 hover:text-red-400 transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-xs text-gray-500">X: {overlay.x}%</label>
                  <input
                    type="range"
                    min={0}
                    max={100}
                    value={overlay.x}
                    onChange={(e) => onUpdate(globalIndex, { ...overlay, x: parseInt(e.target.value) })}
                    className="w-full h-1.5 bg-gray-700 rounded appearance-none cursor-pointer accent-primary-600"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500">Y: {overlay.y}%</label>
                  <input
                    type="range"
                    min={0}
                    max={100}
                    value={overlay.y}
                    onChange={(e) => onUpdate(globalIndex, { ...overlay, y: parseInt(e.target.value) })}
                    className="w-full h-1.5 bg-gray-700 rounded appearance-none cursor-pointer accent-primary-600"
                  />
                </div>
              </div>

              <div className="flex items-center gap-3">
                <select
                  value={overlay.font_size}
                  onChange={(e) => onUpdate(globalIndex, { ...overlay, font_size: parseInt(e.target.value) })}
                  className="px-2 py-1 text-xs bg-gray-800 border border-gray-600 rounded text-gray-200"
                >
                  {FONT_SIZES.map((size) => (
                    <option key={size} value={size}>{size}px</option>
                  ))}
                </select>

                <div className="flex gap-1">
                  {COLORS.map((color) => (
                    <button
                      key={color}
                      type="button"
                      onClick={() => onUpdate(globalIndex, { ...overlay, color })}
                      className={`w-5 h-5 rounded-full border-2 ${
                        overlay.color === color ? 'border-primary-400' : 'border-gray-600'
                      }`}
                      style={{ backgroundColor: color }}
                    />
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
