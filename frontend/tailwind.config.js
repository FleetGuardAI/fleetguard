/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  '#F0FDF4',
          100: '#DCFCE7',
          200: '#BBF7D0',
          300: '#86EFAC',
          400: '#4ADE80',
          500: '#22C55E', // Primary green
          600: '#16A34A',
          700: '#15803D',
          800: '#166534',
          900: '#14532D',
          950: '#052E16',
        },
        surface: {
          DEFAULT: 'var(--surface)',
          secondary: 'var(--surface-secondary)',
          tertiary: 'var(--surface-tertiary)',
          base: 'var(--surface-base)',
          inverted: 'var(--surface-inverted)',
        },
        content: {
          DEFAULT: 'var(--content)',
          secondary: 'var(--content-secondary)',
          muted: 'var(--content-muted)',
        },
        border: {
          DEFAULT: 'var(--border-color)',
        },
        // ── FleetGuard Green Identity ──
        fg: {
          green:         '#22C55E',
          'green-bright':'#86EFAC',
          'green-deep':  '#DCFCE7',
          'green-muted': '#BBF7D0',
          'green-surface':'#F0FDF4',
          text:          '#17201A',
          'text-sec':    '#647067',
          border:        '#E5EDE7',
        },
      },
      boxShadow: {
        card: '0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.02)',
        elevated: '0 8px 24px rgba(0, 0, 0, 0.06), 0 4px 8px rgba(0, 0, 0, 0.03)',
        green: '0 4px 14px rgba(34, 197, 94, 0.12)',
        // FleetGuard accent shadows
        'fg-glow':     '0 4px 20px rgba(34, 197, 94, 0.06)',
        'fg-glow-md':  '0 4px 30px rgba(34, 197, 94, 0.10)',
        'fg-card':     '0 1px 3px rgba(0, 0, 0, 0.04)',
        'fg-elevated': '0 8px 24px rgba(0, 0, 0, 0.06)',
        'fg-active':   '0 0 12px rgba(34, 197, 94, 0.10)',
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
