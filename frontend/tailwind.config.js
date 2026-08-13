/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  '#e8f5e9',
          100: '#c8e6c9',
          200: '#a5d6a7',
          300: '#66bb6a',
          400: '#00e676', // Neon vibrant green
          500: '#00c853', // Primary — vivid green
          600: '#00a844',
          700: '#008837',
          800: '#1b5e20',
          900: '#103e13',
          950: '#0a2e0d',
          850: '#0d4a1a',
        },
        surface: {
          DEFAULT: 'var(--surface)',
          secondary: 'var(--surface-secondary)',
          tertiary: 'var(--surface-tertiary)',
          50:  '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          700: '#1e293b',
          800: '#0f172a',  // Dark slate (cards highlight border)
          850: '#070a0e',  // Deep card background
          900: '#05070a',  // Deeper background
          950: '#0c1017',  // Monitor dashboard slate background
        },
        content: {
          DEFAULT: 'var(--content)',
          secondary: 'var(--content-secondary)',
          muted: 'var(--content-muted)',
        },
        border: {
          DEFAULT: 'var(--border-color)',
        },
        // ── FleetGuard Command-Center Dark Theme ──
        fg: {
          dark:          '#050B09',
          deep:          '#07110D',
          'green-deep':  '#063C28',
          green:         '#19B86A',
          'green-bright':'#36D98A',
          'green-muted': '#0D6B46',
          text:          '#F3F7F5',
          'text-sec':    '#8D9B95',
          card:          'rgba(10,22,17,0.75)',
          border:        'rgba(255,255,255,0.07)',
          'card-hover':  'rgba(14,30,22,0.85)',
        },
      },
      boxShadow: {
        card: '0 4px 24px rgba(0,0,0,0.06)',
        elevated: '0 12px 40px rgba(0,0,0,0.08)',
        green: '0 4px 20px rgba(22,163,74,0.15)',
        // FleetGuard command-center shadows
        'fg-glow':     '0 0 30px rgba(25,184,106,0.08)',
        'fg-glow-md':  '0 0 50px rgba(25,184,106,0.12)',
        'fg-card':     '0 4px 24px rgba(0,0,0,0.3)',
        'fg-elevated': '0 12px 40px rgba(0,0,0,0.4)',
        'fg-active':   '0 0 20px rgba(25,184,106,0.15), inset 0 0 20px rgba(25,184,106,0.05)',
      },
      borderRadius: {
        xl: '16px',
        '2xl': '20px',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      animation: {
        'fade-in': 'fadeIn 0.4s ease-out',
        'slide-in': 'slideIn 0.3s ease-out',
        'slide-up': 'slideUp 0.4s ease-out',
        shimmer: 'shimmer 2s infinite linear',
        'spin-slow': 'spin 2s linear infinite',
        'pulse-slow': 'pulse 3s ease-in-out infinite',
        'typing-dot': 'typingDot 1.4s infinite ease-in-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideIn: {
          from: { opacity: '0', transform: 'translateX(-10px)' },
          to: { opacity: '1', transform: 'translateX(0)' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        typingDot: {
          '0%, 80%, 100%': { opacity: '0.3', transform: 'scale(0.8)' },
          '40%': { opacity: '1', transform: 'scale(1)' },
        },
      },
    },
  },
  plugins: [],
};
