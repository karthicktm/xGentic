"""RAG (Retrieval-Augmented Generation) service for knowledge base functionality."""

import uuid
from datetime import UTC, datetime
from typing import Any

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.document import Document
from app.services.document_processor import DocumentProcessor
from app.services.providers.embedding_provider import EmbeddingProvider
from app.services.providers.pgvector_provider import PgVectorProvider

logger = structlog.get_logger()


class RAGService:
    """Service for RAG operations: document processing, embedding, and search.

    Orchestrates:
    - Document upload and processing
    - Text extraction and chunking
    - Embedding generation
    - Semantic search
    """

    def __init__(
        self,
        db: AsyncSession,
        embedding_config: dict[str, str] | None = None,
    ) -> None:
        """Initialize RAG service.

        Args:
            db: Async database session
            embedding_config: Embedding configuration with keys:
                - api_key: API key for embedding provider
                - embedding_model: Model name (e.g., text-embedding-3-small)
                - embedding_provider: Provider name (openai or voyage)
        """
        self.db = db
        self.document_processor = DocumentProcessor()
        self._embedding_config = embedding_config
        self._embedding_provider: EmbeddingProvider | None = None
        self.vector_provider = PgVectorProvider(db)
        self.logger = logger.bind(component="rag_service")

    @property
    def embedding_provider(self) -> EmbeddingProvider:
        """Lazy-load embedding provider using configured credentials."""
        if self._embedding_provider is None:
            if not self._embedding_config:
                msg = "Knowledge Base integration not configured. Please add your API credentials in the Integrations page."
                raise ValueError(msg)

            api_key = self._embedding_config.get("api_key")
            if not api_key:
                msg = "API key not configured for Knowledge Base. Please add it in the Integrations page."
                raise ValueError(msg)

            model = self._embedding_config.get("embedding_model", "text-embedding-3-small")
            provider = self._embedding_config.get("embedding_provider", "openai")

            self._embedding_provider = EmbeddingProvider(
                api_key=api_key,
                model=model,
                provider=provider,
            )
        return self._embedding_provider

    async def upload_document(
        self,
        agent_id: uuid.UUID,
        user_id: int,
        filename: str,
        content: bytes,
    ) -> Document:
        """Upload and create a document record.

        Args:
            agent_id: Agent UUID
            user_id: User ID who uploaded the document
            filename: Original filename
            content: File content bytes

        Returns:
            Created Document record (status: pending)
        """
        # Validate file type
        file_type = self.document_processor.get_file_type(filename)
        if not file_type:
            msg = f"Unsupported file type: {filename}"
            raise ValueError(msg)

        # Check file size
        if len(content) > settings.RAG_MAX_FILE_SIZE:
            msg = f"File too large: {len(content)} bytes (max {settings.RAG_MAX_FILE_SIZE})"
            raise ValueError(msg)

        # Check document count limit
        count_result = await self.db.execute(
            select(func.count(Document.id)).where(Document.agent_id == agent_id)
        )
        doc_count = count_result.scalar() or 0
        if doc_count >= settings.RAG_MAX_DOCUMENTS_PER_AGENT:
            msg = f"Document limit reached ({settings.RAG_MAX_DOCUMENTS_PER_AGENT})"
            raise ValueError(msg)

        # Create document record
        document = Document(
            agent_id=agent_id,
            user_id=user_id,
            filename=filename,
            file_type=file_type,
            file_size=len(content),
            status="pending",
        )
        self.db.add(document)
        await self.db.commit()
        await self.db.refresh(document)

        self.logger.info(
            "document_uploaded",
            document_id=str(document.id),
            agent_id=str(agent_id),
            filename=filename,
            file_type=file_type,
            file_size=len(content),
        )

        return document

    async def process_document(
        self,
        document_id: uuid.UUID,
        content: bytes,
    ) -> Document:
        """Process a document: extract text, chunk, and generate embeddings.

        Args:
            document_id: Document UUID
            content: File content bytes

        Returns:
            Updated Document record (status: completed or failed)
        """
        # Get document
        result = await self.db.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()
        if not document:
            msg = f"Document not found: {document_id}"
            raise ValueError(msg)

        # Update status to processing
        document.status = "processing"
        await self.db.commit()

        try:
            # Process document: extract text and chunk
            full_text, chunks = await self.document_processor.process(content, document.filename)

            # Generate embeddings for chunks
            embeddings = await self.embedding_provider.generate_embeddings(chunks)

            # Store chunks with embeddings
            chunk_data = [
                {
                    "index": i,
                    "original_text": text,
                    "translated_text": None,
                    "embedding": emb,
                    "source_language": "en",
                    "translation_status": "not_needed",
                    "use_large": self.embedding_provider.is_large_model,
                }
                for i, (text, emb) in enumerate(zip(chunks, embeddings, strict=True))
            ]
            await self.vector_provider.store_chunks_v2(document_id, chunk_data)

            # Update document status
            document.metadata_ = {
                **(document.metadata_ or {}),
                "content": full_text,
                "embedding_dimensions": self.embedding_provider.dimensions,
            }
            document.chunk_count = len(chunks)
            document.status = "completed"
            document.error_message = None

            await self.db.commit()
            await self.db.refresh(document)

            self.logger.info(
                "document_processed",
                document_id=str(document_id),
                text_length=len(full_text),
                chunk_count=len(chunks),
                embedding_dimensions=self.embedding_provider.dimensions,
            )

            return document

        except Exception as e:
            # Rollback any failed transaction before updating status
            await self.db.rollback()

            # Re-fetch document since the session was rolled back
            result = await self.db.execute(select(Document).where(Document.id == document_id))
            document = result.scalar_one_or_none()

            if document:
                # Update status to failed
                document.status = "failed"
                document.error_message = str(e)[:500]  # Truncate long error messages
                await self.db.commit()

            self.logger.exception(
                "document_processing_failed",
                document_id=str(document_id),
                error=str(e),
            )
            raise

    async def search(
        self,
        agent_id: uuid.UUID,
        query: str,
        top_k: int = 3,
    ) -> list[dict[str, Any]]:
        """Search knowledge base for relevant content.

        Uses hybrid search combining vector similarity and keyword matching,
        fused with Reciprocal Rank Fusion (RRF).

        Args:
            agent_id: Agent UUID
            query: Search query
            top_k: Number of results to return

        Returns:
            List of relevant chunks with similarity scores
        """
        self.logger.info(
            "knowledge_base_search_started",
            agent_id=str(agent_id),
            query=query,
            top_k=top_k,
        )

        # Generate query embedding
        query_embedding = await self.embedding_provider.generate_embedding(query)

        # Run vector search and keyword search sequentially
        vector_results = await self.vector_provider.similarity_search(
            agent_id=agent_id,
            query_embedding=query_embedding,
            top_k=top_k,
        )

        # Keyword search with graceful fallback
        keyword_results: list[dict[str, Any]] = []
        try:
            keyword_results = await self.vector_provider.keyword_search(
                agent_id=agent_id,
                query=query,
                top_k=top_k,
            )
        except Exception:
            self.logger.exception("keyword_search_fallback", agent_id=str(agent_id), query=query)

        self.logger.info(
            "hybrid_search_results",
            agent_id=str(agent_id),
            query=query,
            vector_count=len(vector_results),
            keyword_count=len(keyword_results),
        )

        # Fuse results using Reciprocal Rank Fusion (RRF)
        results = self._fuse_results(vector_results, keyword_results, top_k)

        return results

    @staticmethod
    def _fuse_results(
        vector_results: list[dict[str, Any]],
        keyword_results: list[dict[str, Any]],
        top_k: int,
        k: int = 60,
    ) -> list[dict[str, Any]]:
        """Fuse vector and keyword search results using Reciprocal Rank Fusion.

        RRF score = sum(1 / (k + rank)) across result lists.
        Falls back gracefully when one list is empty.

        Args:
            vector_results: Results from vector similarity search
            keyword_results: Results from keyword full-text search
            top_k: Number of results to return
            k: RRF constant (default 60)

        Returns:
            Fused and deduplicated results sorted by RRF score
        """
        # If only one source has results, return it directly
        if not keyword_results:
            return vector_results[:top_k]
        if not vector_results:
            return keyword_results[:top_k]

        # Build score map keyed by chunk_id
        scores: dict[str, float] = {}
        chunks_map: dict[str, dict[str, Any]] = {}

        for rank, result in enumerate(vector_results):
            cid = result["chunk_id"]
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank + 1)
            chunks_map[cid] = result

        for rank, result in enumerate(keyword_results):
            cid = result["chunk_id"]
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank + 1)
            if cid not in chunks_map:
                chunks_map[cid] = result

        # Sort by fused score descending
        ranked_ids = sorted(scores, key=lambda cid: scores[cid], reverse=True)

        # Return top_k results with fused score
        fused: list[dict[str, Any]] = []
        for cid in ranked_ids[:top_k]:
            entry = {**chunks_map[cid], "similarity": scores[cid]}
            fused.append(entry)

        return fused

    async def delete_document(self, document_id: uuid.UUID) -> bool:
        """Delete a document and its chunks.

        Args:
            document_id: Document UUID

        Returns:
            True if deleted successfully
        """
        result = await self.db.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()
        if not document:
            return False

        # Delete chunks first (cascades via FK but explicit is clearer)
        await self.vector_provider.delete_document_chunks(document_id)

        # Delete document
        await self.db.delete(document)
        await self.db.commit()

        self.logger.info(
            "document_deleted",
            document_id=str(document_id),
        )

        return True

    async def reindex_document(
        self,
        document_id: uuid.UUID,
        content: bytes,
    ) -> Document:
        """Reindex a document: delete old chunks and reprocess.

        Args:
            document_id: Document UUID
            content: File content bytes

        Returns:
            Updated Document record
        """
        # Delete existing chunks
        await self.vector_provider.delete_document_chunks(document_id)

        # Reset document status
        result = await self.db.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()
        if not document:
            msg = f"Document not found: {document_id}"
            raise ValueError(msg)

        document.status = "pending"
        document.chunk_count = 0
        document.metadata_ = {k: v for k, v in (document.metadata_ or {}).items() if k != "content"}
        document.error_message = None
        await self.db.commit()

        # Reprocess
        return await self.process_document(document_id, content)

    async def get_documents(self, agent_id: uuid.UUID) -> list[Document]:
        """Get all documents for an agent.

        Args:
            agent_id: Agent UUID

        Returns:
            List of Document records
        """
        result = await self.db.execute(
            select(Document)
            .where(Document.agent_id == agent_id)
            .order_by(Document.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_document(self, document_id: uuid.UUID) -> Document | None:
        """Get a document by ID.

        Args:
            document_id: Document UUID

        Returns:
            Document record or None
        """
        result = await self.db.execute(select(Document).where(Document.id == document_id))
        return result.scalar_one_or_none()
