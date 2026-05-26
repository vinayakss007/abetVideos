import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { Suspense, lazy } from 'react';

// Mock the api client
vi.mock('../src/api/client', () => ({
  getScenes: vi.fn(),
  submitEdit: vi.fn(),
  getPreviewFrame: vi.fn(),
  searchMedia: vi.fn(),
  default: { get: vi.fn(), post: vi.fn() },
}));

import { getScenes } from '../src/api/client';
import SceneTimeline from '../src/components/editor/SceneTimeline';

const mockScenes = [
  {
    scene_number: 1,
    thumbnail_url: '',
    duration_seconds: 5.0,
    narration: 'First scene narration',
    visual_description: 'First scene visual',
    media_url: null,
  },
  {
    scene_number: 2,
    thumbnail_url: '',
    duration_seconds: 8.0,
    narration: 'Second scene narration',
    visual_description: 'Second scene visual',
    media_url: null,
  },
  {
    scene_number: 3,
    thumbnail_url: '',
    duration_seconds: 4.5,
    narration: 'Third scene narration',
    visual_description: 'Third scene visual',
    media_url: null,
  },
];

describe('EditorPage lazy loading', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the lazy-loaded editor page', async () => {
    const mockedGetScenes = vi.mocked(getScenes);
    mockedGetScenes.mockResolvedValue(mockScenes);

    const EditorPage = lazy(() => import('../src/pages/EditorPage'));

    render(
      <MemoryRouter initialEntries={['/edit/test-video-123']}>
        <Routes>
          <Route path="/edit/:videoId" element={
            <Suspense fallback={<div>Loading...</div>}>
              <EditorPage />
            </Suspense>
          } />
        </Routes>
      </MemoryRouter>
    );

    // Wait for scenes to load
    await waitFor(() => {
      expect(screen.getByText('Video Editor')).toBeInTheDocument();
    });

    expect(mockedGetScenes).toHaveBeenCalledWith('test-video-123');
  });

  it('shows error state when scenes fail to load', async () => {
    const mockedGetScenes = vi.mocked(getScenes);
    mockedGetScenes.mockRejectedValue(new Error('Not found'));

    const EditorPage = lazy(() => import('../src/pages/EditorPage'));

    render(
      <MemoryRouter initialEntries={['/edit/bad-id']}>
        <Routes>
          <Route path="/edit/:videoId" element={
            <Suspense fallback={<div>Loading...</div>}>
              <EditorPage />
            </Suspense>
          } />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Failed to load scenes for this video.')).toBeInTheDocument();
    });
  });
});

describe('SceneTimeline', () => {
  it('renders scene cards for each scene', () => {
    render(
      <SceneTimeline
        scenes={mockScenes}
        selectedIndex={0}
        onSelect={() => {}}
        onReorder={() => {}}
      />
    );

    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('displays scene durations', () => {
    render(
      <SceneTimeline
        scenes={mockScenes}
        selectedIndex={0}
        onSelect={() => {}}
        onReorder={() => {}}
      />
    );

    expect(screen.getByText('5.0s')).toBeInTheDocument();
    expect(screen.getByText('8.0s')).toBeInTheDocument();
    expect(screen.getByText('4.5s')).toBeInTheDocument();
  });

  it('shows no thumbnail placeholder when thumbnail_url is empty', () => {
    render(
      <SceneTimeline
        scenes={mockScenes}
        selectedIndex={0}
        onSelect={() => {}}
        onReorder={() => {}}
      />
    );

    const placeholders = screen.getAllByText('No thumbnail');
    expect(placeholders.length).toBe(3);
  });
});
