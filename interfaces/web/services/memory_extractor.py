"""AI 기반 메모리 자동 추출기."""

import json
import logging
from typing import Optional
from anthropic import Anthropic

from core.memory_service import memory_service
from interfaces.web.models.memory import MemoryType, MemoryCreate
from config.settings import settings

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """대화 턴을 분석하여 기억할 만한 정보를 추출하세요.

사용자 메시지: {user_message}
AI 응답: {assistant_response}

다음 카테고리의 메모리를 추출하세요:
- thinking_pattern: 사용자의 사고 방식, 문제 접근 방법
- record: 사실, 경험, 이벤트 기록
- plan: 계획, 목표, TODO
- context: 대화에서 드러난 상황 맥락
- preference: 선호도, 취향, 스타일

규칙:
1. 일반적인 인사나 의미 없는 대화는 빈 배열을 반환합니다
2. 이미 널리 알려진 상식적인 내용은 제외합니다
3. 사용자 개인에 특화된 정보만 추출합니다
4. confidence는 0.0~1.0 사이 값 (확실할수록 높게)

JSON 배열만 반환하세요 (다른 텍스트 없이):
[
  {{
    "type": "카테고리",
    "category": "세부 분류 (자유 텍스트)",
    "content": "기억할 내용 (상세하게)",
    "summary": "한 줄 요약",
    "confidence": 0.8
  }}
]

추출할 내용이 없으면 빈 배열 [] 을 반환하세요."""


class MemoryExtractor:
    """대화에서 메모리를 자동 추출하는 서비스."""

    def __init__(self):
        api_key = settings.anthropic_api_key
        if api_key:
            self.client = Anthropic(api_key=api_key)
        else:
            self.client = None

    async def extract_and_save(
        self, user_message: str, assistant_response: str
    ) -> list[dict]:
        """대화 턴에서 메모리를 추출하고 저장."""
        if not settings.memory_extraction_enabled:
            return []
        if not self.client:
            return []

        # 너무 짧은 대화는 스킵
        if len(user_message.strip()) < 5:
            return []

        try:
            extracted = await self._extract(user_message, assistant_response)
            saved = []

            for item in extracted:
                # 신뢰도 필터
                confidence = item.get("confidence", 0.5)
                if confidence < settings.memory_confidence_threshold:
                    continue

                # 타입 검증
                try:
                    mem_type = MemoryType(item["type"])
                except (ValueError, KeyError):
                    continue

                # 중복 검사 (FTS 유사도)
                content = item.get("content", "")
                existing = memory_service.search(content[:50], limit=3)
                is_duplicate = any(
                    self._is_similar(content, e.content) for e in existing
                )

                if is_duplicate:
                    # 기존 메모리 confidence 업데이트
                    for e in existing:
                        if self._is_similar(content, e.content):
                            from interfaces.web.models.memory import MemoryUpdate
                            new_confidence = min(1.0, e.confidence + 0.05)
                            memory_service.update(
                                e.id, MemoryUpdate(confidence=new_confidence)
                            )
                            break
                    continue

                # 신규 메모리 생성
                memory = memory_service.create(MemoryCreate(
                    type=mem_type,
                    category=item.get("category", ""),
                    content=content,
                    summary=item.get("summary", content[:100]),
                    confidence=confidence,
                ))
                saved.append({
                    "id": memory.id,
                    "type": memory.type.value,
                    "summary": memory.summary,
                })

            return saved

        except Exception as e:
            logger.error(f"메모리 추출 실패: {e}")
            return []

    async def _extract(
        self, user_message: str, assistant_response: str
    ) -> list[dict]:
        """Haiku 모델로 메모리 추출."""
        prompt = EXTRACTION_PROMPT.format(
            user_message=user_message,
            assistant_response=assistant_response[:500],  # 응답은 잘라서
        )

        try:
            response = self.client.messages.create(
                model=settings.haiku_model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )

            text = response.content[0].text.strip()

            # JSON 파싱 (코드블록 래핑 처리)
            if text.startswith("```"):
                text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

            return json.loads(text)

        except (json.JSONDecodeError, IndexError, Exception) as e:
            logger.warning(f"메모리 추출 파싱 실패: {e}")
            return []

    def _is_similar(self, a: str, b: str, threshold: float = 0.7) -> bool:
        """간단한 문자열 유사도 검사 (단어 집합 기반 Jaccard)."""
        words_a = set(a.lower().split())
        words_b = set(b.lower().split())
        if not words_a or not words_b:
            return False
        intersection = words_a & words_b
        union = words_a | words_b
        return len(intersection) / len(union) >= threshold


# 전역 인스턴스
memory_extractor = MemoryExtractor()
