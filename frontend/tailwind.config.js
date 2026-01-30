/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Custom dark theme colors
        bg: {
          primary: 'var(--color-bg-primary)',
          secondary: 'var(--color-bg-secondary)',
          tertiary: 'var(--color-bg-tertiary)',
          elevated: 'var(--color-bg-elevated)',
        },
        accent: {
          red: 'var(--color-accent-red)',
          'red-hover': 'var(--color-accent-red-hover)',
          blue: 'var(--color-accent-blue)',
          'blue-hover': 'var(--color-accent-blue-hover)',
          green: 'var(--color-accent-green)',
          orange: 'var(--color-accent-orange)',
          purple: 'var(--color-accent-purple)',
        },
        text: {
          primary: 'var(--color-text-primary)',
          secondary: 'var(--color-text-secondary)',
          tertiary: 'var(--color-text-tertiary)',
        },
        border: {
          DEFAULT: 'var(--color-border)',
          light: 'var(--color-border-light)',
        },
      },
      boxShadow: {
        'sm': 'var(--shadow-sm)',
        'md': 'var(--shadow-md)',
        'lg': 'var(--shadow-lg)',
        'glow': 'var(--shadow-glow)',
        'glow-blue': 'var(--shadow-glow-blue)',
        'glow-green': '0 0 20px rgba(48, 209, 88, 0.15)',
      },
      transitionTimingFunction: {
        'fast': 'var(--transition-fast)',
        'base': 'var(--transition-base)',
        'slow': 'var(--transition-slow)',
        'bounce': 'var(--transition-bounce)',
      },
      animation: {
        'slide-up': 'slide-up-fade 0.5s ease forwards',
        'scale-in': 'scale-in 0.3s ease forwards',
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
        'shimmer': 'shimmer 1.5s infinite',
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
      },
    },
  },
  plugins: [],
}
