import { useEffect } from 'react';
import { ChatContainer } from './components/Chat';
import { BrainGraph } from './components/Graph';
import { useUIStore } from './stores/uiStore';

function App() {
  const { mobileView, setMobileView, isMobile, windowWidth, updateWindowSize } = useUIStore();

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
        </div>
      )}

      {/* 메인 컨텐츠 영역 */}
      <div className="flex flex-1 min-h-0">
        {/* 그래프 영역 */}
        <div
          style={{
            display: isMobile ? (mobileView === 'graph' ? 'flex' : 'none') : 'flex',
            flex: 1,
            height: '100%'
          }}
        >
          <BrainGraph />
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
