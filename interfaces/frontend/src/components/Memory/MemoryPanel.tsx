import { useEffect, useState, useCallback } from 'react';
import {
  useMemoryStore,
  fetchMemories,
  fetchMemoryStats,
  searchMemories,
  deleteMemory,
} from '../../stores/memoryStore';
import { MemoryItem } from './MemoryItem';
import type { MemoryType } from '../../types';
import { MEMORY_TYPE_META } from '../../types';

interface MemoryPanelProps {
  onClose?: () => void;
}

const MEMORY_TYPES: MemoryType[] = [
  'thinking_pattern',
  'record',
  'plan',
  'context',
  'preference',
];

export function MemoryPanel({ onClose }: MemoryPanelProps) {
  const {
    memories,
    stats,
    selectedMemory,
    searchQuery,
    setMemories,
    setStats,
    selectMemory,
    setSearchQuery,
  } = useMemoryStore();

  const [activeFilter, setActiveFilter] = useState<MemoryType | null>(null);
  const [isSearching, setIsSearching] = useState(false);

  // 초기 데이터 로드
  useEffect(() => {
    loadMemories();
    fetchMemoryStats().then(setStats).catch(() => {});
  }, []);

  const loadMemories = useCallback(async (type?: MemoryType | null) => {
    try {
      const data = await fetchMemories(type || undefined);
      setMemories(data);
    } catch {
      // ignore
    }
  }, [setMemories]);

  // 필터 변경
  const handleFilterChange = (type: MemoryType | null) => {
    setActiveFilter(type);
    setSearchQuery('');
    loadMemories(type);
  };

  // 검색
  const handleSearch = useCallback(async (query: string) => {
    setSearchQuery(query);
    if (!query.trim()) {
      loadMemories(activeFilter);
      return;
    }
    setIsSearching(true);
    try {
      const results = await searchMemories(query);
      setMemories(results);
    } catch {
      // ignore
    } finally {
      setIsSearching(false);
    }
  }, [activeFilter, loadMemories, setMemories, setSearchQuery]);

  // 삭제
  const handleDelete = async (id: string) => {
    try {
      await deleteMemory(id);
      setMemories(memories.filter((m) => m.id !== id));
      if (selectedMemory?.id === id) selectMemory(null);
      fetchMemoryStats().then(setStats).catch(() => {});
    } catch {
      // ignore
    }
  };

  return (
    <div className="flex flex-col h-full bg-zinc-950">
      {/* 헤더 */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800">
        <div className="flex items-center gap-2">
          <span className="text-lg">🧠</span>
          <h2 className="text-sm font-semibold text-zinc-200">메모리</h2>
          {stats && (
            <span className="text-xs text-zinc-500">
              {stats.active}개
            </span>
          )}
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="text-zinc-500 hover:text-zinc-300 transition-colors"
          >
            ✕
          </button>
        )}
      </div>

      {/* 통계 바 */}
      {stats && stats.active > 0 && (
        <div className="flex gap-1 px-4 py-2 border-b border-zinc-800/50">
          {MEMORY_TYPES.map((type) => {
            const count = stats.by_type[type] || 0;
            if (count === 0) return null;
            const meta = MEMORY_TYPE_META[type];
            return (
              <div
                key={type}
                className="flex items-center gap-1 text-xs text-zinc-400"
                title={`${meta.label}: ${count}개`}
              >
                <span>{meta.icon}</span>
                <span>{count}</span>
              </div>
            );
          })}
        </div>
      )}

      {/* 검색 */}
      <div className="px-4 py-2 border-b border-zinc-800/50">
        <div className="relative">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            placeholder="기억 검색..."
            className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-1.5
                       text-sm text-zinc-300 placeholder-zinc-600
                       focus:outline-none focus:border-violet-500/50"
          />
          {isSearching && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2">
              <div className="w-3 h-3 border border-violet-400 border-t-transparent rounded-full animate-spin" />
            </div>
          )}
        </div>
      </div>

      {/* 타입 필터 */}
      <div className="flex gap-1 px-4 py-2 overflow-x-auto border-b border-zinc-800/50">
        <button
          onClick={() => handleFilterChange(null)}
          className={`px-2 py-1 rounded-full text-xs whitespace-nowrap transition-colors ${
            activeFilter === null
              ? 'bg-violet-500/20 text-violet-400'
              : 'text-zinc-500 hover:text-zinc-300'
          }`}
        >
          전체
        </button>
        {MEMORY_TYPES.map((type) => {
          const meta = MEMORY_TYPE_META[type];
          return (
            <button
              key={type}
              onClick={() => handleFilterChange(type)}
              className={`px-2 py-1 rounded-full text-xs whitespace-nowrap transition-colors ${
                activeFilter === type
                  ? 'text-white'
                  : 'text-zinc-500 hover:text-zinc-300'
              }`}
              style={activeFilter === type ? { backgroundColor: meta.color + '30', color: meta.color } : {}}
            >
              {meta.icon} {meta.label}
            </button>
          );
        })}
      </div>

      {/* 메모리 목록 */}
      <div className="flex-1 overflow-y-auto px-4 py-2 space-y-2">
        {memories.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-32 text-zinc-600 text-sm">
            <span className="text-2xl mb-2">🧠</span>
            <p>아직 기억이 없습니다</p>
            <p className="text-xs mt-1">대화하면 자동으로 기억이 쌓입니다</p>
          </div>
        ) : (
          memories.map((memory) => (
            <MemoryItem
              key={memory.id}
              memory={memory}
              isSelected={selectedMemory?.id === memory.id}
              onSelect={selectMemory}
              onDelete={handleDelete}
            />
          ))
        )}
      </div>
    </div>
  );
}
