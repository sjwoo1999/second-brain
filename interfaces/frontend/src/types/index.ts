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
  | 'cost_update';

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
  data?: GraphData | CostInfo;
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
