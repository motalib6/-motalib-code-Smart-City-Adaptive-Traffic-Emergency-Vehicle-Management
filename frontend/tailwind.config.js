/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#0B1220',
        panel: '#111A2E',
        panel2: '#16223A',
        line: '#1E2C47',
        teal: { DEFAULT: '#15C6B3', dark: '#0EA08F' },
        cyanx: '#38BDF8',
        slate2: '#94A3B8',
        danger: '#F87171',
        amberx: '#FBBF24',
        ok: '#34D399',
      },
      fontFamily: { sans: ['Inter', 'system-ui', 'sans-serif'] },
    },
  },
  plugins: [],
};
