/**
 * Tauri 환경 관련 유틸리티
 */

declare global {
  interface Window {
    __TAURI__?: {
      invoke: (cmd: string, args?: Record<string, unknown>) => Promise<unknown>;
    };
  }
}

/**
 * 현재 환경이 Tauri 데스크톱 앱인지 확인
 */
export function isTauri(): boolean {
  return '__TAURI__' in window && window.__TAURI__ !== undefined;
}

/**
 * Tauri invoke 호출 (Tauri 환경에서만 동작)
 */
export async function tauriInvoke<T>(
  cmd: string,
  args?: Record<string, unknown>
): Promise<T | null> {
  if (!isTauri() || !window.__TAURI__) {
    console.warn(`Tauri invoke called in non-Tauri environment: ${cmd}`);
    return null;
  }
  return window.__TAURI__.invoke(cmd, args) as Promise<T>;
}

/**
 * 백엔드 URL 생성
 */
export function getBackendUrl(): string {
  const host = isTauri() ? 'localhost' : window.location.hostname;
  const port = import.meta.env.VITE_BACKEND_PORT || '8000';
  return `http://${host}:${port}`;
}

/**
 * WebSocket URL 생성
 */
export function getWebSocketUrl(): string {
  const host = isTauri() ? 'localhost' : window.location.hostname;
  const port = import.meta.env.VITE_WS_PORT || '8000';
  return `ws://${host}:${port}/ws`;
}
