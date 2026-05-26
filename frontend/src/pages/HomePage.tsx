import { Link } from 'react-router-dom';
import { Sparkles, Video, Mic, Images, Clapperboard } from 'lucide-react';

const FEATURES = [
  {
    icon: Sparkles,
    title: 'AI Script Generation',
    description: 'Enter a topic and get a professionally structured video script in seconds.',
  },
  {
    icon: Mic,
    title: 'Text-to-Speech',
    description: 'Convert your script narration to natural-sounding voice-over audio.',
  },
  {
    icon: Images,
    title: 'Smart Media Sourcing',
    description: 'Automatically find relevant images, GIFs, and stock footage for each scene.',
  },
  {
    icon: Clapperboard,
    title: 'Video Assembly',
    description: 'Combine everything into a polished video ready for sharing.',
  },
];

export default function HomePage() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
      {/* Hero Section */}
      <section className="text-center py-16 sm:py-24">
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary-900/30 border border-primary-700/50 rounded-full text-primary-300 text-sm mb-6">
          <Video className="w-4 h-4" />
          AI-Powered Video Generation
        </div>
        <h1 className="text-4xl sm:text-6xl font-bold mb-6">
          <span className="bg-gradient-to-r from-primary-400 via-blue-400 to-primary-400 bg-clip-text text-transparent">
            Create Videos
          </span>
          <br />
          <span className="text-gray-100">with AI in Minutes</span>
        </h1>
        <p className="text-lg sm:text-xl text-gray-400 max-w-2xl mx-auto mb-10">
          Transform any topic into an engaging video. AI writes the script, generates voice-over,
          finds visual media, and assembles everything into a finished video.
        </p>
        <Link
          to="/create"
          className="inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-primary-600 to-blue-600 hover:from-primary-500 hover:to-blue-500 text-white font-semibold rounded-xl transition-all text-lg shadow-lg shadow-primary-600/25"
        >
          <Sparkles className="w-5 h-5" />
          Create Your First Video
        </Link>
      </section>

      {/* Features Grid */}
      <section className="py-16">
        <h2 className="text-2xl font-bold text-center text-gray-100 mb-12">How It Works</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {FEATURES.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <div
                key={index}
                className="p-6 bg-gray-800/50 border border-gray-700 rounded-xl hover:border-primary-600/50 transition-colors"
              >
                <div className="p-3 bg-primary-600/10 rounded-lg w-fit mb-4">
                  <Icon className="w-6 h-6 text-primary-400" />
                </div>
                <h3 className="font-semibold text-gray-100 mb-2">{feature.title}</h3>
                <p className="text-sm text-gray-400">{feature.description}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* Steps Section */}
      <section className="py-16">
        <h2 className="text-2xl font-bold text-center text-gray-100 mb-12">Simple 4-Step Process</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {['Enter Topic', 'Edit Script', 'Review Media', 'Get Video'].map((label, i) => (
            <div key={i} className="text-center">
              <div className="inline-flex items-center justify-center w-12 h-12 bg-primary-600/20 border border-primary-600/30 rounded-full text-primary-400 font-bold text-lg mb-3">
                {i + 1}
              </div>
              <p className="font-medium text-gray-200">{label}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
