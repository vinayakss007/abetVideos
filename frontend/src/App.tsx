import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Layout from './components/Layout';
import HomePage from './pages/HomePage';
import CreateVideo from './pages/CreateVideo';

const EditorPage = lazy(() => import('./pages/EditorPage'));

function App() {
  return (
    <BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#1f2937',
            color: '#f3f4f6',
            border: '1px solid #374151',
          },
        }}
      />
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/create" element={<CreateVideo />} />
          <Route path="/edit/:videoId" element={
            <Suspense fallback={<div className="flex items-center justify-center min-h-screen"><div className="text-gray-400">Loading Editor...</div></div>}>
              <EditorPage />
            </Suspense>
          } />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
