import type { Memory } from '../../types';
import { MEMORY_TYPE_META } from '../../types';

interface MemoryItemProps {
  memory: Memory;
  isSelected: boolean;
  onSelect: (memory: Memory) => void;
  onDelete: (id: string) => void;
}

export function MemoryItem({ memory, isSelected, onSelect, onDelete }: MemoryItemProps) {
  const meta = MEMORY_TYPE_META[memory.type];
  const date = new Date(memory.updated_at);
  const timeAgo = getTimeAgo(date);

  return (
    <div
      onClick={() => onSelect(memory)}
      className={`p-3 rounded-lg cursor-pointer transition-all border ${
        isSelected
          ? 'border-violet-500/50 bg-violet-500/10'
          : 'border-zinc-800 bg-zinc-900/50 hover:border-zinc-700 hover:bg-zinc-800/50'
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-sm flex-shrink-0">{meta.icon}</span>
          <span
            className="text-xs px-1.5 py-0.5 rounded-full flex-shrink-0"
            style={{ backgroundColor: meta.color + '20', color: meta.color }}
          >
            {meta.label}
          </span>
        </div>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete(memory.id);
          }}
          className="text-zinc-600 hover:text-red-400 transition-colors text-xs flex-shrink-0"
          title="삭제"
        >
          ✕
        </button>
      </div>

      <p className="text-sm text-zinc-300 mt-2 line-clamp-2">
        {memory.summary || memory.content}
      </p>

      <div className="flex items-center justify-between mt-2 text-xs text-zinc-500">
        <span>{timeAgo}</span>
        <div className="flex items-center gap-2">
          {memory.category && (
            <span className="text-zinc-600">#{memory.category}</span>
          )}
          <span className="text-zinc-600">
            {Math.round(memory.confidence * 100)}%
          </span>
        </div>
      </div>

      {/* 선택 시 전체 내용 표시 */}
      {isSelected && memory.content !== memory.summary && (
        <div className="mt-3 pt-3 border-t border-zinc-800">
          <p className="text-sm text-zinc-400 whitespace-pre-wrap">
            {memory.content}
          </p>
        </div>
      )}
    </div>
  );
}

function getTimeAgo(date: Date): string {
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);

  if (minutes < 1) return '방금';
  if (minutes < 60) return `${minutes}분 전`;
  if (hours < 24) return `${hours}시간 전`;
  if (days < 7) return `${days}일 전`;
  return date.toLocaleDateString('ko-KR');
}
