/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
        display: ['Orbitron', 'sans-serif'],
      },
      colors: {
        hud: {
          green: '#00ff88',
          cyan: '#00d4ff',
          yellow: '#ffcc00',
          orange: '#ff8800',
          red: '#ff3366',
          panel: 'rgba(0,20,40,0.85)',
        },
      },
    },
  },
  plugins: [],
}
