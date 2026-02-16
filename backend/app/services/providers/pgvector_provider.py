"""PostgreSQL pgvector provider for vector storage and similarity search."""

# ruff: noqa: S608 - embedding_col is controlled internally, not user input

import uuid
from typing import Any

import structlog
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import DocumentChunk

logger = structlog.get_logger()


class PgVectorProvider:
    """Provider for vector storage and similarity search using pgvector.

    Handles:
    - Storing document chunk embeddings
    - Similarity search using cosine distance
    - Retrieving relevant chunks for RAG queries

    Note: This provider works with the xGentic DocumentChunk model which stores
    content in the `content` column and metadata in a JSON `metadata` column.
    Embedding vectors should be stored in metadata or a dedicated vector column
    added via migration.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize with database session.

        Args:
            db: Async database session
        """
        self.db = db
        self.logger = logger.bind(component="pgvector_provider")

    async def store_chunks(
        self,
        document_id: uuid.UUID,
        chunks: list[tuple[int, str, list[float]]],
    ) -> int:
        """Store document chunks with embeddings.

        Args:
            document_id: UUID of the parent document
            chunks: List of (chunk_index, content_text, embedding) tuples

        Returns:
            Number of chunks stored
        """
        if not chunks:
            return 0

        try:
            for chunk_index, content_text, embedding in chunks:
                chunk = DocumentChunk(
                    document_id=document_id,
                    chunk_index=chunk_index,
                    content=content_text,
                    token_count=len(content_text.split()),
                    metadata_={"embedding": embedding},
                )
                self.db.add(chunk)

            await self.db.flush()

            self.logger.info(
                "chunks_stored",
                document_id=str(document_id),
                chunk_count=len(chunks),
            )
            return len(chunks)
        except Exception:
            self.logger.exception(
                "chunk_storage_failed",
                document_id=str(document_id),
                chunk_count=len(chunks),
            )
            raise

    async def store_chunks_v2(
        self,
        document_id: uuid.UUID,
        chunks: list[dict[str, Any]],
    ) -> int:
        """Store document chunks with embedding data.

        Args:
            document_id: UUID of the parent document
            chunks: List of chunk dictionaries with keys:
                - index: Chunk position in document
                - original_text: Original text content
                - translated_text: English translation (or None if same as original)
                - embedding: Embedding vector
                - source_language: Source language code
                - translation_status: Status of translation
                - use_large: Whether using large embedding model

        Returns:
            Number of chunks stored
        """
        if not chunks:
            return 0

        try:
            for chunk_data in chunks:
                chunk = DocumentChunk(
                    document_id=document_id,
                    chunk_index=chunk_data["index"],
                    content=chunk_data["original_text"],
                    token_count=len(chunk_data["original_text"].split()),
                    metadata_={
                        "embedding": chunk_data["embedding"],
                        "translated_text": chunk_data.get("translated_text"),
                        "source_language": chunk_data.get("source_language"),
                        "translation_status": chunk_data.get("translation_status", "not_needed"),
                        "use_large": chunk_data.get("use_large", False),
                    },
                )
                self.db.add(chunk)

            await self.db.flush()

            self.logger.info(
                "chunks_stored_v2",
                document_id=str(document_id),
                chunk_count=len(chunks),
                use_large=chunks[0].get("use_large", False) if chunks else False,
            )
            return len(chunks)
        except Exception:
            self.logger.exception(
                "chunk_storage_v2_failed",
                document_id=str(document_id),
                chunk_count=len(chunks),
            )
            raise

    async def similarity_search(
        self,
        agent_id: uuid.UUID,
        query_embedding: list[float],
        top_k: int = 3,
    ) -> list[dict[str, Any]]:
        """Search for similar chunks using cosine similarity.

        Uses raw SQL with pgvector's cosine distance operator when a vector
        column is available. Falls back to application-level similarity
        computation using embeddings stored in metadata.

        Args:
            agent_id: Agent UUID to scope the search
            query_embedding: Query embedding vector
            top_k: Number of results to return

        Returns:
            List of matching chunks with similarity scores
        """
        try:
            # Retrieve all chunks for the agent's ready documents
            # and compute similarity in Python (until dedicated vector column is added)
            query = text(
                """
                SELECT
                    dc.id,
                    dc.document_id,
                    dc.chunk_index,
                    dc.content,
                    dc.metadata,
                    d.filename
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                WHERE d.agent_id = :agent_id
                  AND d.status = 'completed'
                LIMIT 1000
                """
            )

            result = await self.db.execute(query, {"agent_id": agent_id})
            rows = result.fetchall()

            # Compute cosine similarity in application
            import math

            def cosine_sim(a: list[float], b: list[float]) -> float:
                if len(a) != len(b) or not a:
                    return 0.0
                dot = sum(x * y for x, y in zip(a, b, strict=False))
                norm_a = math.sqrt(sum(x * x for x in a))
                norm_b = math.sqrt(sum(x * x for x in b))
                if norm_a == 0 or norm_b == 0:
                    return 0.0
                return dot / (norm_a * norm_b)

            scored_results = []
            for row in rows:
                metadata = row.metadata or {}
                embedding = metadata.get("embedding")
                if not embedding:
                    continue
                similarity = cosine_sim(query_embedding, embedding)
                scored_results.append(
                    {
                        "chunk_id": str(row.id),
                        "document_id": str(row.document_id),
                        "chunk_index": row.chunk_index,
                        "content": row.content,
                        "source_language": metadata.get("source_language"),
                        "filename": row.filename,
                        "similarity": similarity,
                    }
                )

            # Sort by similarity descending and take top_k
            scored_results.sort(key=lambda x: x["similarity"], reverse=True)
            results = scored_results[:top_k]

            self.logger.info(
                "similarity_search_completed",
                agent_id=str(agent_id),
                top_k=top_k,
                results_found=len(results),
                embedding_dimensions=len(query_embedding),
            )
            return results
        except Exception:
            self.logger.exception(
                "similarity_search_failed",
                agent_id=str(agent_id),
                top_k=top_k,
            )
            raise

    async def keyword_search(
        self,
        agent_id: uuid.UUID,
        query: str,
        top_k: int = 3,
    ) -> list[dict[str, Any]]:
        """Search for chunks using PostgreSQL ILIKE keyword search.

        Performs a simple case-insensitive keyword search across chunk content.

        Args:
            agent_id: Agent UUID to scope the search
            query: Raw search query text
            top_k: Number of results to return

        Returns:
            List of matching chunks with relevance scores
        """
        try:
            # Simple ILIKE search as a fallback (works without full-text search setup)
            sql = text(
                """
                SELECT
                    dc.id,
                    dc.document_id,
                    dc.chunk_index,
                    dc.content,
                    dc.metadata,
                    d.filename
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                WHERE d.agent_id = :agent_id
                  AND d.status = 'completed'
                  AND dc.content ILIKE :query_pattern
                ORDER BY dc.chunk_index
                LIMIT :top_k
                """
            )

            result = await self.db.execute(
                sql,
                {"agent_id": agent_id, "query_pattern": f"%{query}%", "top_k": top_k},
            )
            rows = result.fetchall()

            results = [
                {
                    "chunk_id": str(row.id),
                    "document_id": str(row.document_id),
                    "chunk_index": row.chunk_index,
                    "content": row.content,
                    "source_language": (row.metadata or {}).get("source_language"),
                    "filename": row.filename,
                    "similarity": 1.0,  # Exact keyword match
                }
                for row in rows
            ]

            self.logger.info(
                "keyword_search_completed",
                agent_id=str(agent_id),
                query=query,
                top_k=top_k,
                results_found=len(results),
            )
            return results
        except Exception:
            self.logger.exception(
                "keyword_search_failed",
                agent_id=str(agent_id),
                top_k=top_k,
            )
            raise

    async def delete_document_chunks(self, document_id: uuid.UUID) -> int:
        """Delete all chunks for a document.

        Args:
            document_id: Document UUID

        Returns:
            Number of chunks deleted
        """
        try:
            result = await self.db.execute(
                select(DocumentChunk).where(DocumentChunk.document_id == document_id)
            )
            chunks = list(result.scalars().all())
            count = len(chunks)

            for chunk in chunks:
                await self.db.delete(chunk)

            await self.db.flush()

            self.logger.info(
                "chunks_deleted",
                document_id=str(document_id),
                chunk_count=count,
            )
            return count
        except Exception:
            self.logger.exception(
                "chunk_deletion_failed",
                document_id=str(document_id),
            )
            raise

    async def get_document_chunk_count(self, agent_id: uuid.UUID) -> int:
        """Get total chunk count for an agent.

        Args:
            agent_id: Agent UUID

        Returns:
            Total number of chunks across all agent's documents
        """
        query = text(
            """
            SELECT COUNT(*) as count
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            WHERE d.agent_id = :agent_id
            """
        )
        result = await self.db.execute(query, {"agent_id": agent_id})
        row = result.fetchone()
        if row is None:
            return 0
        count_val = row[0]  # Access by index to avoid Callable type issue
        return int(count_val) if count_val is not None else 0
