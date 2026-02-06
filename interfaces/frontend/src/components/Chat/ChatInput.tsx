import { useState, useRef, useEffect, type KeyboardEvent } from 'react';

interface Props {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export function ChatInput({ onSend, disabled }: Props) {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // 텍스트 영역 높이 자동 조절
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [input]);

  const handleSend = () => {
    const message = input.trim();
    if (message && !disabled) {
      onSend(message);
      setInput('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex gap-2 p-2.5 sm:p-3 border-t border-zinc-800 bg-zinc-900/80">
      <textarea
        ref={textareaRef}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="메시지를 입력하세요..."
        disabled={disabled}
        className="flex-1 bg-zinc-800/80 text-zinc-100 rounded-xl px-3 py-2.5 sm:px-4 resize-none
                   focus:outline-none focus:ring-2 focus:ring-violet-500/50 focus:bg-zinc-800
                   disabled:opacity-50 text-sm placeholder:text-zinc-500
                   border border-zinc-700/50 transition-all"
        rows={1}
      />
      <button
        onClick={handleSend}
        disabled={disabled || !input.trim()}
        className="bg-violet-600 hover:bg-violet-500 active:bg-violet-700 text-white
                   px-3 sm:px-4 py-2.5 rounded-xl
                   disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-violet-600
                   transition-all duration-150
                   flex items-center justify-center min-w-[48px] sm:min-w-[60px]
                   shadow-lg shadow-violet-500/20"
      >
        {disabled ? (
          <div className="flex gap-0.5">
            <span className="w-1 h-1 bg-white/80 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
            <span className="w-1 h-1 bg-white/80 rounded-full animate-bounce" style={{ animationDelay: '100ms' }} />
            <span className="w-1 h-1 bg-white/80 rounded-full animate-bounce" style={{ animationDelay: '200ms' }} />
          </div>
        ) : (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
        )}
      </button>
    </div>
  );
}
