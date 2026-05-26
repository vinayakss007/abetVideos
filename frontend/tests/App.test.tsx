import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import App from '../src/App';
import { BrowserRouter } from 'react-router-dom';
import TopicInput from '../src/components/TopicInput';
import VideoPlayer from '../src/components/VideoPlayer';

describe('App', () => {
  it('renders the home page with hero text', () => {
    render(<App />);
    expect(screen.getByText('Create Videos')).toBeInTheDocument();
    expect(screen.getByText('with AI in Minutes')).toBeInTheDocument();
  });

  it('renders navigation with create video link', () => {
    render(<App />);
    const createLinks = screen.getAllByText('Create Video');
    expect(createLinks.length).toBeGreaterThan(0);
  });

  it('renders the app brand name', () => {
    render(<App />);
    expect(screen.getByText('Abet Videos')).toBeInTheDocument();
  });
});

describe('TopicInput', () => {
  it('renders the topic form with all fields', () => {
    render(
      <BrowserRouter>
        <TopicInput onSubmit={() => {}} isLoading={false} />
      </BrowserRouter>
    );
    expect(screen.getByText('What is your video about?')).toBeInTheDocument();
    expect(screen.getByText('Video Duration')).toBeInTheDocument();
    expect(screen.getByText('Video Style')).toBeInTheDocument();
    expect(screen.getByText('Generate Video Script')).toBeInTheDocument();
  });

  it('renders duration options', () => {
    render(
      <BrowserRouter>
        <TopicInput onSubmit={() => {}} isLoading={false} />
      </BrowserRouter>
    );
    expect(screen.getByText('30 seconds')).toBeInTheDocument();
    expect(screen.getByText('1 minute')).toBeInTheDocument();
    expect(screen.getByText('5 minutes')).toBeInTheDocument();
    expect(screen.getByText('10 minutes')).toBeInTheDocument();
  });

  it('renders style options', () => {
    render(
      <BrowserRouter>
        <TopicInput onSubmit={() => {}} isLoading={false} />
      </BrowserRouter>
    );
    expect(screen.getByText('Educational')).toBeInTheDocument();
    expect(screen.getByText('Entertainment')).toBeInTheDocument();
    expect(screen.getByText('News')).toBeInTheDocument();
    expect(screen.getByText('Tutorial')).toBeInTheDocument();
  });

  it('shows loading state when isLoading is true', () => {
    render(
      <BrowserRouter>
        <TopicInput onSubmit={() => {}} isLoading={true} />
      </BrowserRouter>
    );
    expect(screen.getByText('Generating Script...')).toBeInTheDocument();
  });
});

describe('VideoPlayer', () => {
  it('renders with video result data', () => {
    const mockResult = {
      video_path: '/output/test.mp4',
      video_id: 'test-123',
      duration: 60,
      scenes_count: 3,
    };
    render(
      <BrowserRouter>
        <VideoPlayer result={mockResult} onReset={() => {}} />
      </BrowserRouter>
    );
    expect(screen.getByText('Video Generated!')).toBeInTheDocument();
    expect(screen.getByText('3 scenes - 60s duration')).toBeInTheDocument();
    expect(screen.getByText('Download Video')).toBeInTheDocument();
    expect(screen.getByText('Create Another')).toBeInTheDocument();
  });
});
