import { create } from 'zustand';
import type { ChatMessage } from '../types';

interface ChatStore {
  // 상태
  messages: ChatMessage[];
  isProcessing: boolean;
  isConnected: boolean;

  // 액션
  addMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => void;
  setProcessing: (status: boolean) => void;
  setConnected: (status: boolean) => void;
  clearMessages: () => void;
}

let messageId = 0;

export const useChatStore = create<ChatStore>((set) => ({
  messages: [],
  isProcessing: false,
  isConnected: false,

  addMessage: (message) =>
    set((state) => ({
      messages: [
        ...state.messages,
        {
          ...message,
          id: String(++messageId),
          timestamp: new Date(),
        },
      ],
    })),

  setProcessing: (status) => set({ isProcessing: status }),

  setConnected: (status) => set({ isConnected: status }),

  clearMessages: () => set({ messages: [] }),
}));
