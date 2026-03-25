import { defineConfig } from 'vite';
import preact from '@preact/preset-vite';
import { resolve, join } from 'path';
import { copyFileSync, mkdirSync, readdirSync, statSync } from 'fs';

const isVercel = process.env.VITE_BASE_PATH === '/';

function copyDir(src, dest) {
  mkdirSync(dest, { recursive: true });
  for (const entry of readdirSync(src)) {
    const srcPath = join(src, entry);
    const destPath = join(dest, entry);
    statSync(srcPath).isDirectory()
      ? copyDir(srcPath, destPath)
      : copyFileSync(srcPath, destPath);
  }
}

function docsifyCopyPlugin() {
  return {
    name: 'docsify-copy',
    closeBundle() {
      const src = resolve(__dirname, '../docs/superpowers');
      const dest = resolve(__dirname, 'dist/superpowers');
      copyDir(src, dest);
      console.log('[docsify-copy] copied to dist/superpowers/');
    },
  };
}

export default defineConfig({
  plugins: [preact(), docsifyCopyPlugin()],
  base: process.env.VITE_BASE_PATH || '/',
  build: {
    outDir: isVercel ? 'dist' : resolve(__dirname, '../docs'),
    emptyOutDir: isVercel,
  },
  server: { port: 3000, open: true },
});
