import type { SceneMetadata, SceneTrim } from '../../types';

interface SceneTrimmerProps {
  scene: SceneMetadata;
  trim: SceneTrim | undefined;
  onTrimChange: (start: number, end: number) => void;
}

export default function SceneTrimmer({ scene, trim, onTrimChange }: SceneTrimmerProps) {
  const start = trim?.start_time ?? 0;
  const end = trim?.end_time ?? scene.duration_seconds;

  return (
    <div className="space-y-4 p-4 bg-gray-800 rounded-lg border border-gray-700">
      <h4 className="text-sm font-medium text-gray-200">Trim Scene {scene.scene_number}</h4>

      <div className="space-y-3">
        <div>
          <label className="text-xs text-gray-400 block mb-1">
            Start Time: {start.toFixed(1)}s
          </label>
          <input
            type="range"
            min={0}
            max={scene.duration_seconds}
            step={0.1}
            value={start}
            onChange={(e) => onTrimChange(parseFloat(e.target.value), end)}
            className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-primary-600"
          />
        </div>

        <div>
          <label className="text-xs text-gray-400 block mb-1">
            End Time: {end.toFixed(1)}s
          </label>
          <input
            type="range"
            min={0}
            max={scene.duration_seconds}
            step={0.1}
            value={end}
            onChange={(e) => onTrimChange(start, parseFloat(e.target.value))}
            className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-primary-600"
          />
        </div>

        <div className="flex justify-between text-xs text-gray-500">
          <span>Duration: {(end - start).toFixed(1)}s</span>
          <span>Original: {scene.duration_seconds.toFixed(1)}s</span>
        </div>
      </div>
    </div>
  );
}
