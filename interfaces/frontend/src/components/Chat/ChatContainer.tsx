import { useEffect, useRef } from 'react';
import { useChatStore } from '../../stores/chatStore';
import { useWebSocket } from '../../hooks/useWebSocket';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { CostDashboard } from '../Cost';

export function ChatContainer() {
  const { messages, isProcessing, isConnected } = useChatStore();
  const { sendMessage, clearHistory } = useWebSocket();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { addMessage, clearMessages } = useChatStore();

  // 스크롤 자동 이동
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = (message: string) => {
    addMessage({ role: 'user', content: message });
    sendMessage(message);
  };

  const handleClear = () => {
    clearHistory();
    clearMessages();
  };

  return (
    <div className="flex flex-col h-full w-full bg-zinc-900/50 backdrop-blur">
      {/* 헤더 */}
      <div className="flex items-center justify-between px-3 py-2.5 sm:px-4 sm:py-3 border-b border-zinc-800 bg-zinc-900/80">
        <div className="flex items-center gap-2">
          <h2 className="text-base sm:text-lg font-semibold text-zinc-100">Chat</h2>
          <div className="flex items-center gap-1.5 ml-2">
            <span
              className={`w-2 h-2 rounded-full transition-colors ${
                isConnected ? 'bg-green-500' : 'bg-red-500'
              }`}
            />
            <span className="text-[10px] sm:text-xs text-zinc-500">
              {isConnected ? '연결됨' : '연결 중...'}
            </span>
          </div>
        </div>

        {/* 대화 초기화 버튼 */}
        {messages.length > 0 && (
          <button
            onClick={handleClear}
            className="text-zinc-500 hover:text-zinc-300 text-xs px-2 py-1 rounded-md hover:bg-zinc-800 transition-colors"
          >
            초기화
          </button>
        )}
      </div>

      {/* 메시지 목록 */}
      <div className="flex-1 overflow-y-auto px-3 py-3 sm:px-4 sm:py-4 space-y-1">
        {messages.length === 0 ? (
          <div className="text-center text-zinc-500 mt-8 sm:mt-12">
            <div className="text-4xl sm:text-5xl mb-3">🧠</div>
            <p className="text-sm sm:text-base font-medium">대화를 시작해보세요!</p>
            <p className="text-xs sm:text-sm mt-1 text-zinc-600">
              메시지를 입력하면 노드가 생성됩니다
            </p>
          </div>
        ) : (
          messages.map((msg) => <ChatMessage key={msg.id} message={msg} />)
        )}

        {/* 로딩 상태 */}
        {isProcessing && (
          <div className="flex justify-start mb-3">
            <div className="bg-zinc-800/80 text-zinc-400 px-4 py-2.5 rounded-2xl rounded-bl-sm border border-zinc-700/50">
              <div className="flex items-center gap-2">
                <div className="flex gap-1">
                  <span className="w-1.5 h-1.5 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-1.5 h-1.5 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-1.5 h-1.5 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
                <span className="text-sm">생각 중...</span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* 입력 */}
      <ChatInput onSend={handleSend} disabled={isProcessing} />

      {/* 비용 대시보드 */}
      <CostDashboard />
    </div>
  );
}
