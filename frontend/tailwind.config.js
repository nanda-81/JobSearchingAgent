/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        slate: {
          950: '#090d16', // Sophisticated Slate-950 deep space base layer
          900: '#111827', // Card Slate-900 background
          850: '#1a2235', // Intermediate floating containers
          800: '#1f293d', // Subtle crisp border Slate-800
          700: '#374151', // Accent highlights Slate-700
        },
        accent: {
          primary: '#10b981', // Professional Mint-Emerald primary accent color
          indigoGlow: 'rgba(16, 185, 129, 0.12)',
          violet: '#34d399', // Emerald secondary accent
          violetGlow: 'rgba(52, 211, 153, 0.15)',
        },
        success: '#10b981',
        warning: '#f59e0b',
        danger: '#f43f5e', // Dark Coral/Rose for scrub zone warnings
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        display: ['Outfit', 'sans-serif'],
      },
      scale: {
        '101': '1.01',
      },
      boxShadow: {
        'glow-primary': '0 0 20px rgba(16, 185, 129, 0.15)',
        'glow-success': '0 0 20px rgba(16, 185, 129, 0.12)',
        'glow-danger': '0 0 20px rgba(244, 63, 94, 0.12)',
      }
    },
  },
  plugins: [],
}
