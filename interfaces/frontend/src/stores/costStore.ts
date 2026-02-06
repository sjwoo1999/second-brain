import { create } from 'zustand';

interface LastRequest {
  model: string | null;
  input_tokens: number;
  output_tokens: number;
  cost_usd: number;
  cached: boolean;
  from_local_cache: boolean;
}

interface Routing {
  model: string | null;
  complexity: string | null;
  reason: string | null;
}

interface ModelUsage {
  requests: number;
  input_tokens: number;
  output_tokens: number;
  cost_usd: number;
}

interface SessionStats {
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
  model_usage: Record<string, ModelUsage>;
}

export interface CostInfo {
  last_request: LastRequest;
  routing: Routing;
  session_stats: SessionStats;
}

interface CostStore {
  // 상태
  costInfo: CostInfo | null;
  isVisible: boolean;

  // 액션
  setCostInfo: (info: CostInfo) => void;
  toggleVisibility: () => void;
  setVisibility: (visible: boolean) => void;
}

const initialCostInfo: CostInfo = {
  last_request: {
    model: null,
    input_tokens: 0,
    output_tokens: 0,
    cost_usd: 0,
    cached: false,
    from_local_cache: false,
  },
  routing: {
    model: null,
    complexity: null,
    reason: null,
  },
  session_stats: {
    total_input_tokens: 0,
    total_output_tokens: 0,
    total_cache_write_tokens: 0,
    total_cache_read_tokens: 0,
    total_cost_usd: 0,
    total_requests: 0,
    cache_hits: 0,
    local_cache_hits: 0,
    cache_hit_rate: 0,
    estimated_savings_usd: 0,
    model_usage: {},
  },
};

export const useCostStore = create<CostStore>((set) => ({
  costInfo: initialCostInfo,
  isVisible: true,

  setCostInfo: (info) => set({ costInfo: info }),

  toggleVisibility: () =>
    set((state) => ({ isVisible: !state.isVisible })),

  setVisibility: (visible) => set({ isVisible: visible }),
}));
