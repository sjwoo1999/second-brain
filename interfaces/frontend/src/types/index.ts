// 노드 타입
export type NodeType = 'topic' | 'tool' | 'knowledge' | 'question' | 'insight';

// 그래프 노드
export interface GraphNode {
  id: string;
  type: NodeType;
  label: string;
  content?: string;
  color: string;
  val?: number;
}

// 그래프 엣지
export interface GraphLink {
  source: string;
  target: string;
  label?: string;
}

// 그래프 데이터
export interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

// 채팅 메시지
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

// 메모리 타입
export type MemoryType = 'thinking_pattern' | 'record' | 'plan' | 'context' | 'preference';

// 메모리 엔티티
export interface Memory {
  id: string;
  type: MemoryType;
  category: string;
  content: string;
  summary: string;
  confidence: number;
  access_count: number;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

// 메모리 통계
export interface MemoryStats {
  total: number;
  active: number;
  by_type: Record<string, number>;
  recent_count: number;
  total_conversations: number;
}

// 메모리 타입 메타 (아이콘, 색상, 라벨)
export const MEMORY_TYPE_META: Record<MemoryType, { icon: string; color: string; label: string }> = {
  thinking_pattern: { icon: '🧠', color: '#8B5CF6', label: '사고 패턴' },
  record: { icon: '📝', color: '#3B82F6', label: '기록' },
  plan: { icon: '🎯', color: '#10B981', label: '계획' },
  context: { icon: '💡', color: '#F59E0B', label: '맥락' },
  preference: { icon: '⭐', color: '#EC4899', label: '선호도' },
};

// WebSocket 메시지 타입
export type WSMessageType =
  | 'chat'
  | 'response'
  | 'processing'
  | 'error'
  | 'graph_init'
  | 'graph_update'
  | 'node_added'
  | 'get_graph'
  | 'get_cost'
  | 'clear_history'
  | 'history_cleared'
  | 'cost_update'
  | 'memory_added'
  | 'memory_stats';

// 비용 정보 타입
export interface CostInfo {
  last_request: {
    model: string | null;
    input_tokens: number;
    output_tokens: number;
    cost_usd: number;
    cached: boolean;
    from_local_cache: boolean;
  };
  routing: {
    model: string | null;
    complexity: string | null;
    reason: string | null;
  };
  session_stats: {
    total_input_tokens: number;
    total_output_tokens: number;
    total_cache_write_tokens: number;
    total_cache_read_tokens: number;
    total_cost_usd: number;
    total_requests: number;
    cache_hits: number;
    local_cache_hits: number;
    cache_hit_rate: number;
    estimated_savings_usd: number;
    model_usage: Record<string, {
      requests: number;
      input_tokens: number;
      output_tokens: number;
      cost_usd: number;
    }>;
  };
}

export interface WSMessage {
  type: WSMessageType;
  message?: string;
  data?: GraphData | CostInfo | MemoryStats | Array<{ id: string; type: string; summary: string }>;
  node?: GraphNode;
  status?: 'started' | 'completed';
}

// 노드 색상 맵
export const NODE_COLORS: Record<NodeType, string> = {
  topic: '#8B5CF6',     // 보라
  tool: '#10B981',      // 초록
  knowledge: '#F59E0B', // 노랑
  question: '#3B82F6',  // 파랑
  insight: '#EC4899',   // 핑크
};
