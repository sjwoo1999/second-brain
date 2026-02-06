"""메모리 서비스 - SQLite 기반 개인 메모리 관리."""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path

from interfaces.web.models.memory import (
    Memory, MemoryType, MemoryCreate, MemoryUpdate, MemoryStats
)
from config.settings import settings


class MemoryService:
    """SQLite 기반 메모리 서비스."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or str(settings.base_dir / "data" / "memory.db")
        # data 디렉토리 생성
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """SQLite 연결 반환."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self):
        """테이블 초기화."""
        conn = self._get_conn()
        try:
            # 메모리 테이블
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    category TEXT DEFAULT '',
                    content TEXT NOT NULL,
                    summary TEXT DEFAULT '',
                    confidence REAL DEFAULT 0.8,
                    access_count INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1
                )
            """)

            # FTS5 전문 검색 테이블
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                    content, summary, category,
                    content_rowid='rowid',
                    tokenize='unicode61'
                )
            """)

            # FTS 동기화 트리거 - INSERT
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
                    INSERT INTO memories_fts(rowid, content, summary, category)
                    VALUES (NEW.rowid, NEW.content, NEW.summary, NEW.category);
                END
            """)

            # FTS 동기화 트리거 - UPDATE
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
                    DELETE FROM memories_fts WHERE rowid = OLD.rowid;
                    INSERT INTO memories_fts(rowid, content, summary, category)
                    VALUES (NEW.rowid, NEW.content, NEW.summary, NEW.category);
                END
            """)

            # FTS 동기화 트리거 - DELETE
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
                    DELETE FROM memories_fts WHERE rowid = OLD.rowid;
                END
            """)

            # 대화 기록 테이블
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

            # 인덱스
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_active ON memories(is_active)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_session
                ON conversations(session_id, created_at)
            """)

            conn.commit()
        finally:
            conn.close()

    # ── CRUD ──────────────────────────────────────

    def create(self, data: MemoryCreate) -> Memory:
        """메모리 생성."""
        memory = Memory(
            type=data.type,
            category=data.category,
            content=data.content,
            summary=data.summary or data.content[:100],
            confidence=data.confidence,
        )

        conn = self._get_conn()
        try:
            conn.execute(
                """INSERT INTO memories
                   (id, type, category, content, summary, confidence,
                    access_count, created_at, updated_at, is_active)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    memory.id, memory.type.value, memory.category,
                    memory.content, memory.summary, memory.confidence,
                    0, memory.created_at.isoformat(),
                    memory.updated_at.isoformat(), 1,
                )
            )
            conn.commit()
        finally:
            conn.close()

        return memory

    def get(self, memory_id: str) -> Optional[Memory]:
        """ID로 메모리 조회."""
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM memories WHERE id = ?", (memory_id,)
            ).fetchone()
            if not row:
                return None
            return self._row_to_memory(row)
        finally:
            conn.close()

    def list_memories(
        self,
        type_filter: Optional[MemoryType] = None,
        category: Optional[str] = None,
        active_only: bool = True,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Memory]:
        """메모리 목록 조회."""
        conn = self._get_conn()
        try:
            query = "SELECT * FROM memories WHERE 1=1"
            params: list = []

            if active_only:
                query += " AND is_active = 1"
            if type_filter:
                query += " AND type = ?"
                params.append(type_filter.value)
            if category:
                query += " AND category = ?"
                params.append(category)

            query += " ORDER BY updated_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            rows = conn.execute(query, params).fetchall()
            return [self._row_to_memory(r) for r in rows]
        finally:
            conn.close()

    def update(self, memory_id: str, data: MemoryUpdate) -> Optional[Memory]:
        """메모리 수정."""
        conn = self._get_conn()
        try:
            updates = []
            params = []

            if data.type is not None:
                updates.append("type = ?")
                params.append(data.type.value)
            if data.category is not None:
                updates.append("category = ?")
                params.append(data.category)
            if data.content is not None:
                updates.append("content = ?")
                params.append(data.content)
            if data.summary is not None:
                updates.append("summary = ?")
                params.append(data.summary)
            if data.confidence is not None:
                updates.append("confidence = ?")
                params.append(data.confidence)
            if data.is_active is not None:
                updates.append("is_active = ?")
                params.append(1 if data.is_active else 0)

            if not updates:
                return self.get(memory_id)

            updates.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            params.append(memory_id)

            conn.execute(
                f"UPDATE memories SET {', '.join(updates)} WHERE id = ?",
                params
            )
            conn.commit()
            return self.get(memory_id)
        finally:
            conn.close()

    def delete(self, memory_id: str) -> bool:
        """메모리 소프트 삭제."""
        conn = self._get_conn()
        try:
            result = conn.execute(
                "UPDATE memories SET is_active = 0, updated_at = ? WHERE id = ?",
                (datetime.now().isoformat(), memory_id)
            )
            conn.commit()
            return result.rowcount > 0
        finally:
            conn.close()

    # ── 검색 ──────────────────────────────────────

    def search(self, query: str, limit: int = 20) -> list[Memory]:
        """FTS5 전문 검색."""
        conn = self._get_conn()
        try:
            # FTS5 쿼리 - 특수문자 이스케이프
            safe_query = query.replace('"', '""')
            rows = conn.execute(
                """SELECT m.* FROM memories m
                   JOIN memories_fts f ON m.rowid = f.rowid
                   WHERE memories_fts MATCH ? AND m.is_active = 1
                   ORDER BY rank
                   LIMIT ?""",
                (f'"{safe_query}"', limit)
            ).fetchall()
            return [self._row_to_memory(r) for r in rows]
        except sqlite3.OperationalError:
            # FTS 매치 실패 시 LIKE 검색 폴백
            rows = conn.execute(
                """SELECT * FROM memories
                   WHERE (content LIKE ? OR summary LIKE ?) AND is_active = 1
                   ORDER BY updated_at DESC LIMIT ?""",
                (f"%{query}%", f"%{query}%", limit)
            ).fetchall()
            return [self._row_to_memory(r) for r in rows]
        finally:
            conn.close()

    def retrieve_relevant(self, query: str, limit: int = 10) -> list[Memory]:
        """관련 메모리 검색 - FTS + 최신성 + 접근 빈도 가중 점수."""
        conn = self._get_conn()
        try:
            safe_query = query.replace('"', '""')
            # FTS 랭크 + 최신성(7일 이내 보너스) + 접근 빈도 가중치
            rows = conn.execute(
                """SELECT m.*,
                    (
                        CASE WHEN julianday('now') - julianday(m.updated_at) < 7
                             THEN 2.0 ELSE 1.0 END
                        + m.access_count * 0.1
                    ) as relevance_boost
                   FROM memories m
                   JOIN memories_fts f ON m.rowid = f.rowid
                   WHERE memories_fts MATCH ? AND m.is_active = 1
                   ORDER BY rank * relevance_boost
                   LIMIT ?""",
                (f'"{safe_query}"', limit)
            ).fetchall()

            memories = [self._row_to_memory(r) for r in rows]

            # 접근 카운트 증가
            if memories:
                ids = [m.id for m in memories]
                placeholders = ",".join("?" * len(ids))
                conn.execute(
                    f"UPDATE memories SET access_count = access_count + 1 WHERE id IN ({placeholders})",
                    ids
                )
                conn.commit()

            return memories
        except sqlite3.OperationalError:
            # FTS 실패 시 최신 활성 메모리 반환
            rows = conn.execute(
                """SELECT * FROM memories
                   WHERE is_active = 1
                   ORDER BY updated_at DESC LIMIT ?""",
                (limit,)
            ).fetchall()
            return [self._row_to_memory(r) for r in rows]
        finally:
            conn.close()

    # ── 컨텍스트 빌드 ────────────────────────────

    def build_context(self, user_message: str, token_budget: int = None) -> str:
        """시스템 프롬프트에 주입할 메모리 컨텍스트 빌드."""
        if token_budget is None:
            token_budget = settings.memory_token_budget

        memories = self.retrieve_relevant(user_message, limit=15)
        if not memories:
            return ""

        # 타입별 그룹핑
        groups: dict[str, list[Memory]] = {}
        for m in memories:
            type_label = self._type_label(m.type)
            groups.setdefault(type_label, []).append(m)

        # 포맷팅
        lines = ["\n## 사용자에 대해 기억하고 있는 정보"]
        char_count = 0
        char_limit = token_budget * 4  # 대략적 토큰→문자 변환

        for type_label, mems in groups.items():
            section = f"\n### {type_label}"
            lines.append(section)
            char_count += len(section)

            for m in mems:
                text = f"- {m.summary or m.content[:100]}"
                if char_count + len(text) > char_limit:
                    break
                lines.append(text)
                char_count += len(text)

            if char_count > char_limit:
                break

        return "\n".join(lines)

    # ── 대화 기록 ────────────────────────────────

    def save_conversation(self, session_id: str, role: str, content: str):
        """대화 기록 저장."""
        conn = self._get_conn()
        try:
            conn.execute(
                """INSERT INTO conversations (session_id, role, content, created_at)
                   VALUES (?, ?, ?, ?)""",
                (session_id, role, content, datetime.now().isoformat())
            )
            conn.commit()
        finally:
            conn.close()

    def get_conversations(
        self, session_id: str, limit: int = 50
    ) -> list[dict]:
        """대화 기록 조회."""
        conn = self._get_conn()
        try:
            rows = conn.execute(
                """SELECT role, content, created_at FROM conversations
                   WHERE session_id = ?
                   ORDER BY created_at DESC LIMIT ?""",
                (session_id, limit)
            ).fetchall()
            return [dict(r) for r in reversed(rows)]
        finally:
            conn.close()

    # ── 통계 ──────────────────────────────────────

    def get_stats(self) -> MemoryStats:
        """메모리 통계."""
        conn = self._get_conn()
        try:
            total = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
            active = conn.execute(
                "SELECT COUNT(*) FROM memories WHERE is_active = 1"
            ).fetchone()[0]

            # 타입별 카운트
            rows = conn.execute(
                """SELECT type, COUNT(*) as cnt FROM memories
                   WHERE is_active = 1 GROUP BY type"""
            ).fetchall()
            by_type = {r["type"]: r["cnt"] for r in rows}

            # 최근 24시간
            yesterday = (datetime.now() - timedelta(days=1)).isoformat()
            recent = conn.execute(
                "SELECT COUNT(*) FROM memories WHERE created_at > ? AND is_active = 1",
                (yesterday,)
            ).fetchone()[0]

            # 대화 수
            convs = conn.execute(
                "SELECT COUNT(DISTINCT session_id) FROM conversations"
            ).fetchone()[0]

            return MemoryStats(
                total=total,
                active=active,
                by_type=by_type,
                recent_count=recent,
                total_conversations=convs,
            )
        finally:
            conn.close()

    # ── 헬퍼 ──────────────────────────────────────

    def _row_to_memory(self, row: sqlite3.Row) -> Memory:
        """SQLite Row → Memory 모델 변환."""
        return Memory(
            id=row["id"],
            type=MemoryType(row["type"]),
            category=row["category"],
            content=row["content"],
            summary=row["summary"],
            confidence=row["confidence"],
            access_count=row["access_count"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            is_active=bool(row["is_active"]),
        )

    def _type_label(self, t: MemoryType) -> str:
        """타입 → 한글 라벨."""
        labels = {
            MemoryType.THINKING_PATTERN: "🧠 사고 패턴",
            MemoryType.RECORD: "📝 기록",
            MemoryType.PLAN: "🎯 계획",
            MemoryType.CONTEXT: "💡 맥락",
            MemoryType.PREFERENCE: "⭐ 선호도",
        }
        return labels.get(t, str(t))


# 전역 인스턴스
memory_service = MemoryService()
