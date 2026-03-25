import { defineConfig } from 'vite';
import preact from '@preact/preset-vite';
import { resolve } from 'path';

export default defineConfig({
  plugins: [preact()],
  // Deploy to /AgentBoss/ subdirectory on GitHub Pages
  base: '/AgentBoss/',
  build: {
    outDir: resolve(__dirname, '../docs'),
  },
  server: {
    port: 3000,
    open: true,
  },
});
