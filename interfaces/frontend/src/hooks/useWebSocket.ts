import { useEffect, useRef, useCallback } from 'react';
import { useGraphStore } from '../stores/graphStore';
import { useChatStore } from '../stores/chatStore';
import { useCostStore } from '../stores/costStore';
import { useMemoryStore, fetchMemories, fetchMemoryStats } from '../stores/memoryStore';
import type { WSMessage, GraphData, CostInfo, MemoryStats } from '../types';

// Tauri 환경에서는 localhost:8000 사용, 브라우저에서는 현재 호스트 사용
const isTauri = () => '__TAURI__' in window;
const WS_HOST = isTauri() ? 'localhost' : window.location.hostname;
const WS_PORT = import.meta.env.VITE_WS_PORT || '8000';
const WS_URL = `ws://${WS_HOST}:${WS_PORT}/ws`;

export function useWebSocket() {
  const ws = useRef<WebSocket | null>(null);
  const sessionId = useRef(crypto.randomUUID());

  const { setGraphData, addNode } = useGraphStore();
  const { addMessage, setProcessing, setConnected } = useChatStore();
  const { setCostInfo } = useCostStore();
  const { setStats: setMemoryStats, setMemories } = useMemoryStore();

  // 메시지 핸들러
  const handleMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const message: WSMessage = JSON.parse(event.data);

        switch (message.type) {
          case 'graph_init':
          case 'graph_update':
            if (message.data && 'nodes' in message.data) {
              setGraphData(message.data as GraphData);
            }
            break;

          case 'node_added':
            if (message.node) {
              addNode(message.node);
            }
            break;

          case 'response':
            if (message.message) {
              addMessage({
                role: 'assistant',
                content: message.message,
              });
            }
            break;

          case 'processing':
            setProcessing(message.status === 'started');
            break;

          case 'cost_update':
            if (message.data && 'session_stats' in message.data) {
              setCostInfo(message.data as CostInfo);
            }
            break;

          case 'error':
            console.error('WebSocket error:', message.message);
            addMessage({
              role: 'assistant',
              content: `오류: ${message.message}`,
            });
            setProcessing(false);
            break;

          case 'memory_added':
            // 새 메모리가 추출됨 → 메모리 목록 새로고침
            fetchMemories().then(setMemories).catch(() => {});
            break;

          case 'memory_stats':
            if (message.data && 'active' in message.data) {
              setMemoryStats(message.data as MemoryStats);
            }
            break;

          case 'history_cleared':
            // 처리 완료
            break;
        }
      } catch (e) {
        console.error('Failed to parse message:', e);
      }
    },
    [setGraphData, addNode, addMessage, setProcessing, setCostInfo, setMemoryStats, setMemories]
  );

  // 연결 설정
  useEffect(() => {
    const connect = () => {
      const socket = new WebSocket(`${WS_URL}/${sessionId.current}`);

      socket.onopen = () => {
        console.log('WebSocket connected');
        setConnected(true);
        // 초기 메모리 데이터 로드
        fetchMemoryStats().then(setMemoryStats).catch(() => {});
        fetchMemories().then(setMemories).catch(() => {});
      };

      socket.onclose = () => {
        console.log('WebSocket disconnected');
        setConnected(false);
        // 재연결 시도
        setTimeout(connect, 3000);
      };

      socket.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      socket.onmessage = handleMessage;

      ws.current = socket;
    };

    connect();

    return () => {
      ws.current?.close();
    };
  }, [handleMessage, setConnected]);

  // 메시지 전송
  const sendMessage = useCallback((message: string) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(
        JSON.stringify({
          type: 'chat',
          message,
        })
      );
    }
  }, []);

  // 그래프 요청
  const requestGraph = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type: 'get_graph' }));
    }
  }, []);

  // 비용 정보 요청
  const requestCost = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type: 'get_cost' }));
    }
  }, []);

  // 히스토리 초기화
  const clearHistory = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type: 'clear_history' }));
    }
  }, []);

  return {
    sendMessage,
    requestGraph,
    requestCost,
    clearHistory,
  };
}
