import { useEffect } from 'react';
import { ChatContainer } from './components/Chat';
import { BrainGraph } from './components/Graph';
import { MemoryPanel, MemoryIndicator } from './components/Memory';
import { useUIStore } from './stores/uiStore';

function App() {
  const { mobileView, setMobileView, isMobile, windowWidth, updateWindowSize, isMemoryPanelOpen, toggleMemoryPanel } = useUIStore();

  // Tauri WebView resize 대응
  useEffect(() => {
    const handleResize = () => {
      updateWindowSize(window.innerWidth);
    };

    // 초기 크기 설정
    handleResize();

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [updateWindowSize]);

  // 채팅 영역 너비 계산 (JS 기반)
  const getChatWidth = () => {
    if (isMobile) return '100%';
    if (windowWidth >= 1280) return '480px'; // xl
    if (windowWidth >= 1024) return '420px'; // lg
    return '380px'; // md
  };

  return (
    <div className="flex flex-col h-screen w-screen bg-zinc-950">
      {/* 모바일 탭 네비게이션 */}
      {isMobile && (
        <div className="flex border-b border-zinc-800">
          <button
            onClick={() => setMobileView('graph')}
            className={`flex-1 py-3 text-sm font-medium transition-colors ${
              mobileView === 'graph'
                ? 'text-violet-400 border-b-2 border-violet-400 bg-zinc-900/50'
                : 'text-zinc-500 hover:text-zinc-300'
            }`}
          >
            <span className="mr-2">🧠</span>
            그래프
          </button>
          <button
            onClick={() => setMobileView('chat')}
            className={`flex-1 py-3 text-sm font-medium transition-colors ${
              mobileView === 'chat'
                ? 'text-violet-400 border-b-2 border-violet-400 bg-zinc-900/50'
                : 'text-zinc-500 hover:text-zinc-300'
            }`}
          >
            <span className="mr-2">💬</span>
            채팅
          </button>
          <button
            onClick={() => setMobileView('memory')}
            className={`flex-1 py-3 text-sm font-medium transition-colors ${
              mobileView === 'memory'
                ? 'text-violet-400 border-b-2 border-violet-400 bg-zinc-900/50'
                : 'text-zinc-500 hover:text-zinc-300'
            }`}
          >
            <span className="mr-2">💾</span>
            기억
          </button>
        </div>
      )}

      {/* 메인 컨텐츠 영역 */}
      <div className="flex flex-1 min-h-0">
        {/* 메모리 패널 - 데스크톱: 토글 가능한 왼쪽 드로어 */}
        {!isMobile && isMemoryPanelOpen && (
          <div
            style={{
              width: '320px',
              height: '100%',
              borderRight: '1px solid #27272a',
            }}
          >
            <MemoryPanel onClose={toggleMemoryPanel} />
          </div>
        )}

        {/* 메모리 패널 - 모바일 */}
        {isMobile && mobileView === 'memory' && (
          <div style={{ width: '100%', height: '100%' }}>
            <MemoryPanel />
          </div>
        )}

        {/* 그래프 영역 */}
        <div
          style={{
            display: isMobile ? (mobileView === 'graph' ? 'flex' : 'none') : 'flex',
            flex: 1,
            height: '100%',
            position: 'relative',
          }}
        >
          <BrainGraph />
          {/* 데스크톱: 메모리 패널 토글 + 인디케이터 */}
          {!isMobile && (
            <div className="absolute top-3 left-3 z-10 flex items-center gap-2">
              <button
                onClick={toggleMemoryPanel}
                className={`p-2 rounded-lg transition-colors ${
                  isMemoryPanelOpen
                    ? 'bg-violet-500/20 text-violet-400'
                    : 'bg-zinc-800/80 text-zinc-400 hover:text-zinc-200'
                }`}
                title="메모리 패널"
              >
                💾
              </button>
              <MemoryIndicator onClick={toggleMemoryPanel} />
            </div>
          )}
        </div>

        {/* 채팅 영역 */}
        <div
          style={{
            display: isMobile ? (mobileView === 'chat' ? 'flex' : 'none') : 'flex',
            width: getChatWidth(),
            height: '100%',
            borderLeft: isMobile ? 'none' : '1px solid #27272a'
          }}
        >
          <ChatContainer />
        </div>
      </div>
    </div>
  );
}

export default App;
