"""대화 요약 서비스 - 오래된 대화를 요약하여 토큰 절감."""

from typing import Optional
from anthropic import Anthropic
from config.settings import settings


class ConversationSummarizer:
    """대화 요약기 - 오래된 대화를 압축하여 컨텍스트 토큰 절감."""

    SUMMARY_PROMPT = """아래 대화를 핵심 내용만 추려서 간결하게 요약해주세요.
중요한 정보, 결정사항, 맥락은 반드시 포함하세요.

대화:
{conversation}

요약 (3-5문장):"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.anthropic_api_key
        self.client = Anthropic(api_key=self.api_key)

    def should_summarize(self, history: list[dict]) -> bool:
        """요약이 필요한지 확인."""
        if not settings.cost_optimization.conversation_summarization_enabled:
            return False

        threshold = settings.cost_optimization.summarize_after_messages
        return len(history) > threshold

    def summarize_history(self, history: list[dict]) -> list[dict]:
        """대화 기록 요약.

        Returns:
            [요약 메시지] + [최근 메시지들]
        """
        if not self.should_summarize(history):
            return history

        max_recent = settings.cost_optimization.max_recent_messages

        # 최근 메시지는 유지
        recent_messages = history[-max_recent:]

        # 오래된 메시지 요약
        old_messages = history[:-max_recent]

        if not old_messages:
            return history

        # 요약 생성
        summary = self._generate_summary(old_messages)

        # 요약을 시스템 메시지로 추가
        summarized_history = [
            {
                "role": "user",
                "content": f"[이전 대화 요약]\n{summary}"
            },
            {
                "role": "assistant",
                "content": "네, 이전 대화 내용을 기억하고 있습니다."
            }
        ] + recent_messages

        return summarized_history

    def _generate_summary(self, messages: list[dict]) -> str:
        """메시지들을 요약."""
        # 대화 텍스트 생성
        conversation_text = self._format_conversation(messages)

        # Haiku로 요약 생성 (비용 절감)
        try:
            response = self.client.messages.create(
                model=settings.haiku_model,
                max_tokens=500,
                messages=[{
                    "role": "user",
                    "content": self.SUMMARY_PROMPT.format(conversation=conversation_text)
                }]
            )

            # 텍스트 추출
            for block in response.content:
                if hasattr(block, 'text'):
                    return block.text

            return "대화 요약을 생성하지 못했습니다."

        except Exception as e:
            # 요약 실패 시 간단한 압축
            return self._simple_compress(messages)

    def _format_conversation(self, messages: list[dict]) -> str:
        """메시지들을 텍스트로 포맷."""
        lines = []
        for msg in messages:
            role = "사용자" if msg["role"] == "user" else "AI"
            content = msg.get("content", "")

            # 콘텐츠가 리스트인 경우 (tool use 등)
            if isinstance(content, list):
                text_parts = []
                for item in content:
                    if hasattr(item, 'text'):
                        text_parts.append(item.text)
                    elif isinstance(item, dict) and item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
                content = " ".join(text_parts)

            # 긴 내용 자르기
            if len(content) > 500:
                content = content[:500] + "..."

            lines.append(f"{role}: {content}")

        return "\n".join(lines)

    def _simple_compress(self, messages: list[dict]) -> str:
        """API 호출 실패 시 간단한 압축."""
        topics = []
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str) and len(content) > 20:
                # 첫 50자만 추출
                topics.append(content[:50])

        return "대화 주제: " + ", ".join(topics[:5])

    def estimate_token_savings(self, original_history: list[dict], summarized_history: list[dict]) -> dict:
        """토큰 절감량 추정."""
        # 간단한 추정 (평균 토큰 = 문자 수 / 4)
        original_chars = sum(
            len(str(msg.get("content", ""))) for msg in original_history
        )
        summarized_chars = sum(
            len(str(msg.get("content", ""))) for msg in summarized_history
        )

        original_tokens = original_chars // 4
        summarized_tokens = summarized_chars // 4
        saved_tokens = max(0, original_tokens - summarized_tokens)

        return {
            "original_tokens": original_tokens,
            "summarized_tokens": summarized_tokens,
            "saved_tokens": saved_tokens,
            "savings_percent": (saved_tokens / original_tokens * 100) if original_tokens > 0 else 0
        }


# 전역 요약기 인스턴스
summarizer = ConversationSummarizer()
