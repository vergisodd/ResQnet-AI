import type { Config } from 'tailwindcss';

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#040711',
        navy: '#07111f',
        cyan: '#62e6ff',
        electric: '#3a8bff',
        violet: '#9a7cff',
        amber: '#ffb057'
      },
      borderRadius: {
        ui: '8px'
      },
      boxShadow: {
        glow: '0 0 0 1px rgba(98,230,255,.22), 0 18px 70px rgba(32,180,255,.16)'
      },
      fontFamily: {
        sora: ['Sora', 'Inter', 'ui-sans-serif', 'system-ui', 'sans-serif']
      }
    }
  },
  plugins: []
} satisfies Config;
