import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// Tauri 개발 환경 설정
// https://v2.tauri.app/start/frontend/vite/
const host = process.env.TAURI_DEV_HOST || 'localhost'

export default defineConfig({
  plugins: [react(), tailwindcss()],

  // Vite 빌드 시 기본 경로 설정
  base: './',

  // 프로덕션 빌드 최적화
  build: {
    target: 'esnext',
    minify: 'esbuild',
    sourcemap: false,
  },

  server: {
    host: host,
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/ws': {
        target: 'ws://127.0.0.1:8000',
        ws: true,
      },
    },
    // Tauri 개발 환경에서 HMR 활성화
    hmr: host
      ? {
          protocol: 'ws',
          host: host,
          port: 5173,
        }
      : undefined,
    watch: {
      ignored: ['**/src-tauri/**'],
    },
  },

  // 환경변수 접두사
  envPrefix: ['VITE_', 'TAURI_'],
})
