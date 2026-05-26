interface AudioControlsProps {
  sceneNumber: number;
  volume: number;
  bgMusicVolume: number;
  onVolumeChange: (volume: number) => void;
  onBgMusicVolumeChange: (volume: number) => void;
}

export default function AudioControls({
  sceneNumber,
  volume,
  bgMusicVolume,
  onVolumeChange,
  onBgMusicVolumeChange,
}: AudioControlsProps) {
  const volumePercent = Math.round(volume * 100);
  const bgPercent = Math.round(bgMusicVolume * 100);

  return (
    <div className="space-y-4 p-4 bg-gray-800 rounded-lg border border-gray-700">
      <h4 className="text-sm font-medium text-gray-200">Audio Controls - Scene {sceneNumber}</h4>

      <div className="space-y-3">
        <div>
          <label className="text-xs text-gray-400 block mb-1">
            Scene Volume: {volumePercent}%
          </label>
          <input
            type="range"
            min={0}
            max={2}
            step={0.05}
            value={volume}
            onChange={(e) => onVolumeChange(parseFloat(e.target.value))}
            className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-primary-600"
          />
          <div className="mt-1 h-2 bg-gray-900 rounded overflow-hidden">
            <div
              className="h-full bg-green-500 transition-all"
              style={{ width: `${Math.min(volumePercent, 100)}%` }}
            />
          </div>
        </div>

        <div>
          <label className="text-xs text-gray-400 block mb-1">
            Background Music: {bgPercent}%
          </label>
          <input
            type="range"
            min={0}
            max={1}
            step={0.05}
            value={bgMusicVolume}
            onChange={(e) => onBgMusicVolumeChange(parseFloat(e.target.value))}
            className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-primary-600"
          />
          <div className="mt-1 h-2 bg-gray-900 rounded overflow-hidden">
            <div
              className="h-full bg-blue-500 transition-all"
              style={{ width: `${bgPercent}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
