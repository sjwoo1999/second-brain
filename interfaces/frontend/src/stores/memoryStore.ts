import { create } from 'zustand';
import type { Memory, MemoryStats } from '../types';

interface MemoryStore {
  // 상태
  memories: Memory[];
  stats: MemoryStats | null;
  searchResults: Memory[];
  selectedMemory: Memory | null;
  isLoading: boolean;
  searchQuery: string;

  // 액션
  setMemories: (memories: Memory[]) => void;
  addMemory: (memory: Memory) => void;
  setStats: (stats: MemoryStats) => void;
  setSearchResults: (results: Memory[]) => void;
  selectMemory: (memory: Memory | null) => void;
  setLoading: (loading: boolean) => void;
  setSearchQuery: (query: string) => void;
}

// API 베이스 URL
const isTauri = () => '__TAURI__' in window;
const API_HOST = isTauri() ? 'localhost' : window.location.hostname;
const API_PORT = import.meta.env.VITE_WS_PORT || '8000';
const API_BASE = `http://${API_HOST}:${API_PORT}`;

export const useMemoryStore = create<MemoryStore>((set) => ({
  memories: [],
  stats: null,
  searchResults: [],
  selectedMemory: null,
  isLoading: false,
  searchQuery: '',

  setMemories: (memories) => set({ memories }),
  addMemory: (memory) =>
    set((state) => ({
      memories: [memory, ...state.memories],
    })),
  setStats: (stats) => set({ stats }),
  setSearchResults: (results) => set({ searchResults: results }),
  selectMemory: (memory) => set({ selectedMemory: memory }),
  setLoading: (loading) => set({ isLoading: loading }),
  setSearchQuery: (query) => set({ searchQuery: query }),
}));

// API 헬퍼 함수들
export async function fetchMemories(type?: string): Promise<Memory[]> {
  const params = new URLSearchParams();
  if (type) params.set('type', type);
  params.set('limit', '100');
  const res = await fetch(`${API_BASE}/api/memory/?${params}`);
  return res.json();
}

export async function fetchMemoryStats(): Promise<MemoryStats> {
  const res = await fetch(`${API_BASE}/api/memory/stats`);
  return res.json();
}

export async function searchMemories(query: string): Promise<Memory[]> {
  const res = await fetch(`${API_BASE}/api/memory/search?q=${encodeURIComponent(query)}`);
  return res.json();
}

export async function deleteMemory(id: string): Promise<void> {
  await fetch(`${API_BASE}/api/memory/${id}`, { method: 'DELETE' });
}
