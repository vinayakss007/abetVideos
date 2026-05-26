import { useState, useCallback, useEffect, useRef } from 'react';
import type {
  SceneMetadata,
  EditInstruction,
  SceneTrim,
  TextOverlayInstruction,
  SceneAudioLevel,
} from '../types';
import { submitEdit } from '../api/client';

interface UseEditorReturn {
  scenes: SceneMetadata[];
  setScenes: (scenes: SceneMetadata[]) => void;
  selectedSceneIndex: number;
  editInstructions: EditInstruction;
  isSubmitting: boolean;
  isDirty: boolean;
  reorderScenes: (fromIndex: number, toIndex: number) => void;
  selectScene: (index: number) => void;
  updateTrim: (sceneNumber: number, start: number, end: number) => void;
  addOverlay: (overlay: TextOverlayInstruction) => void;
  removeOverlay: (index: number) => void;
  updateOverlay: (index: number, overlay: TextOverlayInstruction) => void;
  setAudioLevel: (sceneNumber: number, volume: number) => void;
  setBgMusicVolume: (volume: number) => void;
  submitEdits: (videoId: string) => Promise<{ video_id: string; video_path: string; duration_seconds: number } | null>;
  reset: () => void;
}

function createDefaultInstructions(): EditInstruction {
  return {
    scene_order: [],
    trims: [],
    text_overlays: [],
    audio_levels: [],
    background_music_volume: 0.3,
  };
}

export function useEditor(): UseEditorReturn {
  const [scenes, setScenesState] = useState<SceneMetadata[]>([]);
  const [selectedSceneIndex, setSelectedSceneIndex] = useState(0);
  const [editInstructions, setEditInstructions] = useState<EditInstruction>(createDefaultInstructions());
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDirty, setIsDirty] = useState(false);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const setScenes = useCallback((newScenes: SceneMetadata[]) => {
    setScenesState(newScenes);
    setEditInstructions((prev) => ({
      ...prev,
      scene_order: newScenes.map((s) => s.scene_number),
    }));
  }, []);

  const reorderScenes = useCallback((fromIndex: number, toIndex: number) => {
    setScenesState((prev) => {
      const updated = [...prev];
      const [moved] = updated.splice(fromIndex, 1);
      updated.splice(toIndex, 0, moved);
      setEditInstructions((instr) => ({
        ...instr,
        scene_order: updated.map((s) => s.scene_number),
      }));
      return updated;
    });
    setIsDirty(true);
  }, []);

  const selectScene = useCallback((index: number) => {
    setSelectedSceneIndex(index);
  }, []);

  const updateTrim = useCallback((sceneNumber: number, start: number, end: number) => {
    setEditInstructions((prev) => {
      const trims = prev.trims.filter((t) => t.scene_number !== sceneNumber);
      const newTrim: SceneTrim = { scene_number: sceneNumber, start_time: start, end_time: end };
      return { ...prev, trims: [...trims, newTrim] };
    });
    setIsDirty(true);
  }, []);

  const addOverlay = useCallback((overlay: TextOverlayInstruction) => {
    setEditInstructions((prev) => ({
      ...prev,
      text_overlays: [...prev.text_overlays, overlay],
    }));
    setIsDirty(true);
  }, []);

  const removeOverlay = useCallback((index: number) => {
    setEditInstructions((prev) => ({
      ...prev,
      text_overlays: prev.text_overlays.filter((_, i) => i !== index),
    }));
    setIsDirty(true);
  }, []);

  const updateOverlay = useCallback((index: number, overlay: TextOverlayInstruction) => {
    setEditInstructions((prev) => {
      const overlays = [...prev.text_overlays];
      overlays[index] = overlay;
      return { ...prev, text_overlays: overlays };
    });
    setIsDirty(true);
  }, []);

  const setAudioLevel = useCallback((sceneNumber: number, volume: number) => {
    setEditInstructions((prev) => {
      const levels = prev.audio_levels.filter((a) => a.scene_number !== sceneNumber);
      const newLevel: SceneAudioLevel = { scene_number: sceneNumber, volume };
      return { ...prev, audio_levels: [...levels, newLevel] };
    });
    setIsDirty(true);
  }, []);

  const setBgMusicVolume = useCallback((volume: number) => {
    setEditInstructions((prev) => ({ ...prev, background_music_volume: volume }));
    setIsDirty(true);
  }, []);

  const submitEdits = useCallback(async (videoId: string) => {
    setIsSubmitting(true);
    try {
      const result = await submitEdit(videoId, editInstructions);
      if (mountedRef.current) {
        setIsDirty(false);
      }
      return result;
    } catch {
      return null;
    } finally {
      if (mountedRef.current) {
        setIsSubmitting(false);
      }
    }
  }, [editInstructions]);

  const reset = useCallback(() => {
    setScenesState([]);
    setSelectedSceneIndex(0);
    setEditInstructions(createDefaultInstructions());
    setIsDirty(false);
    setIsSubmitting(false);
  }, []);

  return {
    scenes,
    setScenes,
    selectedSceneIndex,
    editInstructions,
    isSubmitting,
    isDirty,
    reorderScenes,
    selectScene,
    updateTrim,
    addOverlay,
    removeOverlay,
    updateOverlay,
    setAudioLevel,
    setBgMusicVolume,
    submitEdits,
    reset,
  };
}
