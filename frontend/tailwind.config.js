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
          50:  '#ecfdf5',
          100: '#d1fae5',
          200: '#a7f3d0',
          300: '#6ee7b7',
          400: '#10b981', // Vibrant emerald
          500: '#059669',
          600: '#047857',
          700: '#065f46',
          800: '#166534',
          900: '#14532d',
          950: '#052e16',
          850: '#022c22',
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
      },
      boxShadow: {
        card: '0 4px 24px rgba(0,0,0,0.06)',
        elevated: '0 12px 40px rgba(0,0,0,0.08)',
        green: '0 4px 20px rgba(22,163,74,0.15)',
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
      },
    },
  },
  plugins: [],
};
