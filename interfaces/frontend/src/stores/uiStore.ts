import { create } from 'zustand';

type MobileView = 'graph' | 'chat';

interface UIStore {
  // 모바일 뷰 상태
  mobileView: MobileView;
  setMobileView: (view: MobileView) => void;
  toggleMobileView: () => void;

  // 사이드바 상태
  isSidebarOpen: boolean;
  toggleSidebar: () => void;

  // 범례 표시 상태
  showLegend: boolean;
  toggleLegend: () => void;

  // 화면 크기 상태 (Tauri WebView 대응)
  windowWidth: number;
  isMobile: boolean;
  updateWindowSize: (width: number) => void;
}

const MD_BREAKPOINT = 768;

export const useUIStore = create<UIStore>((set) => ({
  mobileView: 'chat',
  setMobileView: (view) => set({ mobileView: view }),
  toggleMobileView: () =>
    set((state) => ({
      mobileView: state.mobileView === 'graph' ? 'chat' : 'graph',
    })),

  isSidebarOpen: true,
  toggleSidebar: () =>
    set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),

  showLegend: true,
  toggleLegend: () =>
    set((state) => ({ showLegend: !state.showLegend })),

  windowWidth: typeof window !== 'undefined' ? window.innerWidth : 1024,
  isMobile: typeof window !== 'undefined' ? window.innerWidth < MD_BREAKPOINT : false,
  updateWindowSize: (width) => set({
    windowWidth: width,
    isMobile: width < MD_BREAKPOINT
  }),
}));
