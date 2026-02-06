import { useMemoryStore } from '../../stores/memoryStore';

interface MemoryIndicatorProps {
  onClick?: () => void;
}

export function MemoryIndicator({ onClick }: MemoryIndicatorProps) {
  const { stats } = useMemoryStore();

  if (!stats || stats.active === 0) return null;

  return (
    <button
      onClick={onClick}
      className="flex items-center gap-1.5 px-2 py-1 rounded-full
                 bg-violet-500/10 text-violet-400 text-xs
                 hover:bg-violet-500/20 transition-colors"
      title="메모리 패널 열기"
    >
      <span className="w-1.5 h-1.5 rounded-full bg-violet-400 animate-pulse" />
      <span>{stats.active}개 기억</span>
    </button>
  );
}
