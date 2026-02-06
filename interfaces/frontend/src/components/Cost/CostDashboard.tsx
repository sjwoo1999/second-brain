import { useCostStore } from '../../stores/costStore';

// 모델 이름 축약
function getModelShortName(model: string | null): string {
  if (!model) return '-';
  if (model.includes('opus')) return 'Opus';
  if (model.includes('sonnet')) return 'Sonnet';
  if (model.includes('haiku')) return 'Haiku';
  return model;
}

// 복잡도 한글화
function getComplexityLabel(complexity: string | null): string {
  switch (complexity) {
    case 'simple':
      return '간단';
    case 'normal':
      return '일반';
    case 'complex':
      return '복잡';
    default:
      return '-';
  }
}

// 복잡도 색상
function getComplexityColor(complexity: string | null): string {
  switch (complexity) {
    case 'simple':
      return 'text-green-400';
    case 'normal':
      return 'text-blue-400';
    case 'complex':
      return 'text-orange-400';
    default:
      return 'text-zinc-400';
  }
}

// 숫자 포맷팅
function formatNumber(num: number): string {
  if (num >= 1000000) return (num / 1000000).toFixed(2) + 'M';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
  return num.toString();
}

// 비용 포맷팅 (USD)
function formatCost(cost: number): string {
  if (cost < 0.0001) return '$0.00';
  if (cost < 0.01) return '$' + cost.toFixed(4);
  return '$' + cost.toFixed(3);
}

export function CostDashboard() {
  const { costInfo, isVisible, toggleVisibility } = useCostStore();

  if (!costInfo) return null;

  const { last_request, routing, session_stats } = costInfo;
  const totalTokens = last_request.input_tokens + last_request.output_tokens;

  // 캐시 상태 배지
  const getCacheBadge = () => {
    if (last_request.from_local_cache) {
      return (
        <span className="px-1.5 py-0.5 text-[9px] sm:text-[10px] bg-emerald-500/20 text-emerald-400 rounded-full font-medium">
          LOCAL
        </span>
      );
    }
    if (last_request.cached) {
      return (
        <span className="px-1.5 py-0.5 text-[9px] sm:text-[10px] bg-blue-500/20 text-blue-400 rounded-full font-medium">
          CACHED
        </span>
      );
    }
    return null;
  };

  return (
    <div className="bg-zinc-900/95 border-t border-zinc-800">
      {/* 토글 버튼 */}
      <button
        onClick={toggleVisibility}
        className="w-full px-3 py-2 flex items-center justify-between text-zinc-400 hover:bg-zinc-800/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <svg className="w-3.5 h-3.5 text-zinc-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <span className="text-xs font-medium">비용</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-emerald-400">
            {formatCost(session_stats.total_cost_usd)}
          </span>
          <svg
            className={`w-3.5 h-3.5 transition-transform ${isVisible ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {isVisible && (
        <div className="px-3 pb-3 space-y-2">
          {/* 마지막 요청 요약 */}
          <div className="bg-zinc-800/50 rounded-lg p-2.5 border border-zinc-700/30">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] text-zinc-500 uppercase tracking-wider font-medium">
                마지막 요청
              </span>
              {getCacheBadge()}
            </div>

            <div className="flex items-center justify-between">
              {/* 모델 & 복잡도 */}
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-violet-400">
                  {getModelShortName(routing.model)}
                </span>
                <span className={`text-[10px] ${getComplexityColor(routing.complexity)}`}>
                  {getComplexityLabel(routing.complexity)}
                </span>
              </div>

              {/* 토큰 & 비용 */}
              <div className="flex items-center gap-3 text-xs">
                <span className="text-zinc-400">
                  <span className="text-zinc-300 font-medium">{formatNumber(totalTokens)}</span> tok
                </span>
                <span className="text-emerald-400 font-semibold">
                  {formatCost(last_request.cost_usd)}
                </span>
              </div>
            </div>
          </div>

          {/* 세션 통계 그리드 */}
          <div className="grid grid-cols-4 gap-1.5">
            {/* 총 토큰 */}
            <div className="bg-zinc-800/50 rounded-lg p-2 text-center border border-zinc-700/30">
              <div className="text-sm sm:text-base font-bold text-blue-400">
                {formatNumber(session_stats.total_input_tokens + session_stats.total_output_tokens)}
              </div>
              <div className="text-[9px] sm:text-[10px] text-zinc-500 mt-0.5">토큰</div>
            </div>

            {/* 요청 수 */}
            <div className="bg-zinc-800/50 rounded-lg p-2 text-center border border-zinc-700/30">
              <div className="text-sm sm:text-base font-bold text-violet-400">
                {session_stats.total_requests}
              </div>
              <div className="text-[9px] sm:text-[10px] text-zinc-500 mt-0.5">요청</div>
            </div>

            {/* 캐시 히트율 */}
            <div className="bg-zinc-800/50 rounded-lg p-2 text-center border border-zinc-700/30">
              <div className="text-sm sm:text-base font-bold text-emerald-400">
                {session_stats.cache_hit_rate.toFixed(0)}%
              </div>
              <div className="text-[9px] sm:text-[10px] text-zinc-500 mt-0.5">캐시</div>
            </div>

            {/* 절감액 */}
            <div className="bg-zinc-800/50 rounded-lg p-2 text-center border border-zinc-700/30">
              <div className="text-sm sm:text-base font-bold text-green-400">
                {formatCost(session_stats.estimated_savings_usd)}
              </div>
              <div className="text-[9px] sm:text-[10px] text-zinc-500 mt-0.5">절감</div>
            </div>
          </div>

          {/* 모델별 사용량 (있을 경우만) */}
          {Object.keys(session_stats.model_usage).length > 1 && (
            <div className="bg-zinc-800/50 rounded-lg p-2 border border-zinc-700/30">
              <div className="text-[10px] text-zinc-500 uppercase tracking-wider font-medium mb-1.5">
                모델별 사용
              </div>
              <div className="space-y-1">
                {Object.entries(session_stats.model_usage).map(([model, usage]) => (
                  <div
                    key={model}
                    className="flex items-center justify-between text-[11px] sm:text-xs"
                  >
                    <span className="text-zinc-400 font-medium">
                      {getModelShortName(model)}
                    </span>
                    <div className="flex items-center gap-2">
                      <span className="text-zinc-500">{usage.requests}회</span>
                      <span className="text-emerald-400 font-medium">
                        {formatCost(usage.cost_usd)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
