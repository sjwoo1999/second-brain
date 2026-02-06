"""MemoryExtractor 단위 테스트."""

import json
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from interfaces.web.services.memory_extractor import MemoryExtractor
from interfaces.web.models.memory import MemoryType, MemoryCreate
from config.settings import settings


class TestMemoryExtractorSimilarity:
    """_is_similar Jaccard 유사도 테스트."""

    def setup_method(self):
        """테스트용 인스턴스 생성 (client 없이)."""
        with patch.object(settings, "anthropic_api_key", ""):
            self.extractor = MemoryExtractor()

    def test_identical_strings(self):
        """동일 문자열 → True."""
        assert self.extractor._is_similar("hello world", "hello world") is True

    def test_similar_strings(self):
        """유사 문자열 → True (threshold=0.7)."""
        assert self.extractor._is_similar(
            "Python 프로그래밍 학습 중",
            "Python 프로그래밍 학습",
        ) is True

    def test_different_strings(self):
        """다른 문자열 → False."""
        assert self.extractor._is_similar(
            "Python 프로그래밍",
            "자바스크립트 웹 개발 프론트엔드",
        ) is False

    def test_empty_strings(self):
        """빈 문자열 → False."""
        assert self.extractor._is_similar("", "") is False
        assert self.extractor._is_similar("hello", "") is False

    def test_custom_threshold(self):
        """커스텀 threshold."""
        # 낮은 threshold → 더 쉽게 유사 판정
        assert self.extractor._is_similar(
            "a b c d", "a b x y", threshold=0.3
        ) is True
        # 높은 threshold → 더 엄격
        assert self.extractor._is_similar(
            "a b c d", "a b x y", threshold=0.9
        ) is False


class TestMemoryExtractorParsing:
    """API 응답 JSON 파싱 테스트."""

    @pytest.fixture
    def extractor_with_mock(self, mock_anthropic):
        """Mock Anthropic client가 있는 extractor."""
        with patch.object(settings, "anthropic_api_key", "test-key"):
            ext = MemoryExtractor()
            ext.client = mock_anthropic
            return ext

    @pytest.mark.asyncio
    async def test_parse_json_response(self, extractor_with_mock):
        """JSON 응답 파싱."""
        response_data = [
            {
                "type": "record",
                "category": "tech",
                "content": "Python을 좋아한다",
                "summary": "Python 선호",
                "confidence": 0.9,
            }
        ]
        extractor_with_mock.client.messages.create.return_value.content = [
            MagicMock(text=json.dumps(response_data, ensure_ascii=False))
        ]

        with patch("interfaces.web.services.memory_extractor.memory_service") as mock_ms:
            mock_ms.search.return_value = []
            mock_memory = MagicMock()
            mock_memory.id = "test-id"
            mock_memory.type = MemoryType.RECORD
            mock_memory.summary = "Python 선호"
            mock_ms.create.return_value = mock_memory

            result = await extractor_with_mock.extract_and_save(
                "Python이 좋아", "Python은 좋은 언어입니다."
            )
            assert len(result) == 1
            assert result[0]["summary"] == "Python 선호"

    @pytest.mark.asyncio
    async def test_parse_code_block_json(self, extractor_with_mock):
        """코드 블록으로 래핑된 JSON 파싱."""
        response_data = [{"type": "record", "category": "", "content": "test content here", "summary": "test summary", "confidence": 0.8}]
        code_block = f"```json\n{json.dumps(response_data)}\n```"
        extractor_with_mock.client.messages.create.return_value.content = [
            MagicMock(text=code_block)
        ]

        with patch("interfaces.web.services.memory_extractor.memory_service") as mock_ms:
            mock_ms.search.return_value = []
            mock_memory = MagicMock()
            mock_memory.id = "test-id"
            mock_memory.type = MemoryType.RECORD
            mock_memory.summary = "test summary"
            mock_ms.create.return_value = mock_memory

            # user_message must be >= 5 chars to not be skipped
            result = await extractor_with_mock.extract_and_save("longer message here", "resp " * 10)
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_parse_invalid_json(self, extractor_with_mock):
        """잘못된 JSON → 빈 리스트."""
        extractor_with_mock.client.messages.create.return_value.content = [
            MagicMock(text="this is not json")
        ]

        result = await extractor_with_mock.extract_and_save("msg", "resp " * 10)
        assert result == []


class TestMemoryExtractorFiltering:
    """신뢰도 필터링 및 중복 감지 테스트."""

    @pytest.fixture
    def extractor_with_mock(self, mock_anthropic):
        with patch.object(settings, "anthropic_api_key", "test-key"):
            ext = MemoryExtractor()
            ext.client = mock_anthropic
            return ext

    @pytest.mark.asyncio
    async def test_low_confidence_filtered(self, extractor_with_mock):
        """신뢰도 낮은 항목 필터링."""
        response_data = [
            {"type": "record", "category": "", "content": "test", "summary": "test", "confidence": 0.3}
        ]
        extractor_with_mock.client.messages.create.return_value.content = [
            MagicMock(text=json.dumps(response_data))
        ]

        with patch("interfaces.web.services.memory_extractor.memory_service") as mock_ms:
            mock_ms.search.return_value = []

            result = await extractor_with_mock.extract_and_save("msg", "resp " * 10)
            assert len(result) == 0
            mock_ms.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_invalid_type_filtered(self, extractor_with_mock):
        """잘못된 타입 필터링."""
        response_data = [
            {"type": "invalid_type", "category": "", "content": "test", "summary": "test", "confidence": 0.9}
        ]
        extractor_with_mock.client.messages.create.return_value.content = [
            MagicMock(text=json.dumps(response_data))
        ]

        with patch("interfaces.web.services.memory_extractor.memory_service") as mock_ms:
            mock_ms.search.return_value = []
            result = await extractor_with_mock.extract_and_save("msg", "resp " * 10)
            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_duplicate_detection_updates_confidence(self, extractor_with_mock):
        """중복 감지 시 기존 메모리 confidence 업데이트."""
        response_data = [
            {"type": "record", "category": "", "content": "Python을 좋아한다", "summary": "Python 선호", "confidence": 0.9}
        ]
        extractor_with_mock.client.messages.create.return_value.content = [
            MagicMock(text=json.dumps(response_data, ensure_ascii=False))
        ]

        # 기존 유사 메모리가 있는 경우
        existing_memory = MagicMock()
        existing_memory.id = "existing-id"
        existing_memory.content = "Python을 좋아한다"
        existing_memory.confidence = 0.8

        with patch("interfaces.web.services.memory_extractor.memory_service") as mock_ms:
            mock_ms.search.return_value = [existing_memory]

            result = await extractor_with_mock.extract_and_save(
                "Python이 좋아", "좋은 선택입니다 " * 5
            )
            # 중복이므로 새로 생성되지 않음
            assert len(result) == 0
            # confidence가 업데이트됨
            mock_ms.update.assert_called_once()


class TestMemoryExtractorDisabled:
    """비활성화 테스트."""

    @pytest.mark.asyncio
    async def test_disabled_returns_empty(self):
        """추출 비활성화 시 빈 리스트."""
        original = settings.memory_extraction_enabled
        try:
            settings.memory_extraction_enabled = False
            with patch.object(settings, "anthropic_api_key", "test-key"):
                ext = MemoryExtractor()
                result = await ext.extract_and_save("hello", "world")
                assert result == []
        finally:
            settings.memory_extraction_enabled = original

    @pytest.mark.asyncio
    async def test_no_client_returns_empty(self):
        """API 키 없으면 빈 리스트."""
        with patch.object(settings, "anthropic_api_key", ""):
            ext = MemoryExtractor()
            result = await ext.extract_and_save("hello", "world")
            assert result == []

    @pytest.mark.asyncio
    async def test_short_message_skipped(self):
        """짧은 메시지 스킵."""
        with patch.object(settings, "anthropic_api_key", "test-key"):
            ext = MemoryExtractor()
            ext.client = MagicMock()
            result = await ext.extract_and_save("hi", "hello")
            assert result == []
            ext.client.messages.create.assert_not_called()
