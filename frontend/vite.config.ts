import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

export default defineConfig({
  base: './',
  plugins: [react()],
  build: {
    outDir: '../static/dashboard-react',
    emptyOutDir: true,
    modulePreload: false,
    rollupOptions: {
      output: {
        manualChunks(id) {
          const normalizedId = id.replaceAll('\\', '/');
          if (!normalizedId.includes('/node_modules/')) return undefined;

          if (normalizedId.includes('/react/') || normalizedId.includes('/react-dom/')) {
            return 'react';
          }

          if (normalizedId.includes('/gsap/') || normalizedId.includes('/@gsap/react/')) {
            return 'gsap';
          }

          if (
            normalizedId.includes('/@react-three/postprocessing/') ||
            normalizedId.includes('/postprocessing/')
          ) {
            return 'postprocessing';
          }

          if (normalizedId.includes('/@react-three/fiber/')) {
            return 'r3f';
          }

          if (
            normalizedId.includes('/@react-three/drei/') ||
            normalizedId.includes('/three-stdlib/') ||
            normalizedId.includes('/stats-gl/') ||
            normalizedId.includes('/maath/')
          ) {
            return 'drei';
          }

          if (normalizedId.includes('/three/')) {
            return 'three';
          }

          return undefined;
        }
      }
    }
  }
});
