import type { ChatMessage as MessageType } from '../../types';

interface Props {
  message: MessageType;
}

export function ChatMessage({ message }: Props) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-2 sm:mb-3`}>
      <div
        className={`max-w-[85%] sm:max-w-[80%] px-3 py-2 sm:px-4 sm:py-2.5 rounded-2xl ${
          isUser
            ? 'bg-violet-600 text-white rounded-br-md shadow-lg shadow-violet-500/10'
            : 'bg-zinc-800/80 text-zinc-100 rounded-bl-md border border-zinc-700/50'
        }`}
      >
        <p className="text-[13px] sm:text-sm whitespace-pre-wrap leading-relaxed">
          {message.content}
        </p>
        <span
          className={`text-[10px] mt-1.5 block ${
            isUser ? 'text-violet-200/60' : 'text-zinc-500'
          }`}
        >
          {message.timestamp.toLocaleTimeString('ko-KR', {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </span>
      </div>
    </div>
  );
}
