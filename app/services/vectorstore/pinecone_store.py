"""
Pinecone vector store implementation.

Provides index management, vector upsert, and deletion operations
with namespace support and automatic retry logic.
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from pinecone import Pinecone, ServerlessSpec
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from app.config import settings

logger = logging.getLogger(__name__)


class PineconeStore:
    """
    Pinecone vector store wrapper.
    
    Features:
    - Automatic index creation with serverless spec
    - Namespace-based multi-tenancy
    - Batched upserts with retry logic
    - Flexible deletion by ID, filter, or namespace
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        index_name: Optional[str] = None,
        dimension: Optional[int] = None,
        metric: str = "cosine",
        cloud: Optional[str] = None,
        region: Optional[str] = None,
    ):
        """
        Initialize Pinecone store.
        
        Args:
            api_key: Pinecone API key (defaults to settings)
            index_name: Index name (defaults to settings)
            dimension: Vector dimension (defaults to settings)
            metric: Distance metric (cosine, euclidean, dotproduct)
            cloud: Cloud provider (aws, gcp, azure)
            region: Cloud region
        """
        self.api_key = api_key or settings.pinecone_api_key
        self.index_name = index_name or settings.pinecone_index_name
        self.dimension = dimension or settings.pinecone_dimension
        self.metric = metric or settings.pinecone_metric
        self.cloud = cloud or settings.pinecone_cloud
        self.region = region or settings.pinecone_region
        
        if not self.api_key:
            raise ValueError(
                "Pinecone API key is required. Set PINECONE_API_KEY environment variable."
            )
        
        # Initialize Pinecone client
        self.pc = Pinecone(api_key=self.api_key)
        
        # Ensure index exists
        self._ensure_index()
        
        # Get index instance
        self.index = self.pc.Index(self.index_name)
        
        logger.info(
            f"Initialized Pinecone store: index={self.index_name}, "
            f"dimension={self.dimension}, metric={self.metric}"
        )
    
    def _ensure_index(self) -> None:
        """
        Ensure the Pinecone index exists, create if not.
        
        Raises:
            ValueError: If existing index has mismatched dimension
        """
        existing_indexes = self.pc.list_indexes()
        index_names = [idx.name for idx in existing_indexes]
        
        if self.index_name in index_names:
            # Validate dimension matches
            index_info = self.pc.describe_index(self.index_name)
            existing_dim = index_info.dimension
            
            if existing_dim != self.dimension:
                raise ValueError(
                    f"Index '{self.index_name}' exists with dimension {existing_dim} "
                    f"but provider expects {self.dimension}. "
                    f"Please either:\n"
                    f"1. Delete the existing index and recreate it, or\n"
                    f"2. Update PINECONE_DIMENSION={existing_dim} to match, or\n"
                    f"3. Use a different index name via PINECONE_INDEX_NAME"
                )
            
            logger.info(f"Using existing Pinecone index: {self.index_name}")
        else:
            # Create new serverless index
            logger.info(
                f"Creating Pinecone index: {self.index_name} "
                f"(dimension={self.dimension}, metric={self.metric}, "
                f"cloud={self.cloud}, region={self.region})"
            )
            
            self.pc.create_index(
                name=self.index_name,
                dimension=self.dimension,
                metric=self.metric,
                spec=ServerlessSpec(
                    cloud=self.cloud,
                    region=self.region
                )
            )
            
            logger.info(f"Created Pinecone index: {self.index_name}")
    
    def build_namespace(
        self,
        upload_id: UUID,
        tenant_id: Optional[str] = None
    ) -> str:
        """
        Build namespace string for multi-tenancy.
        
        Args:
            upload_id: Upload batch UUID
            tenant_id: Optional tenant identifier
            
        Returns:
            Namespace string
        """
        if tenant_id:
            return f"tenant:{tenant_id}|upload:{upload_id}"
        return f"upload:{upload_id}"
    
    def build_vector_id(self, chunk_id: UUID) -> str:
        """
        Build deterministic vector ID from chunk ID.
        
        Args:
            chunk_id: Chunk UUID
            
        Returns:
            Vector ID string
        """
        return f"chunk:{chunk_id}"
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def upsert_vectors(
        self,
        vectors: List[tuple],
        namespace: str,
        batch_size: Optional[int] = None
    ) -> Dict[str, int]:
        """
        Upsert vectors to Pinecone with retry logic.
        
        Args:
            vectors: List of (id, embedding, metadata) tuples
            namespace: Namespace for the vectors
            batch_size: Batch size for upserts (defaults to settings)
            
        Returns:
            Dict with upsert statistics
            
        Raises:
            Exception: If upsert fails after retries
        """
        if not vectors:
            return {"upserted": 0}
        
        effective_batch_size = batch_size or settings.upsert_batch_size
        
        logger.info(
            f"Upserting {len(vectors)} vectors to namespace '{namespace}' "
            f"in batches of {effective_batch_size}"
        )
        
        total_upserted = 0
        
        # Process in batches
        for i in range(0, len(vectors), effective_batch_size):
            batch = vectors[i:i + effective_batch_size]
            
            try:
                response = self.index.upsert(
                    vectors=batch,
                    namespace=namespace
                )
                
                upserted = response.get("upserted_count", len(batch))
                total_upserted += upserted
                
                logger.debug(
                    f"Upserted batch {i//effective_batch_size + 1}: "
                    f"{upserted} vectors"
                )
                
            except Exception as e:
                logger.error(f"Error upserting batch: {e}")
                raise
        
        logger.info(
            f"Successfully upserted {total_upserted} vectors to namespace '{namespace}'"
        )
        
        return {"upserted": total_upserted}
    
    def delete_by_ids(
        self,
        vector_ids: List[str],
        namespace: str
    ) -> None:
        """
        Delete vectors by IDs.
        
        Args:
            vector_ids: List of vector IDs to delete
            namespace: Namespace containing the vectors
        """
        if not vector_ids:
            return
        
        logger.info(
            f"Deleting {len(vector_ids)} vectors from namespace '{namespace}'"
        )
        
        try:
            self.index.delete(
                ids=vector_ids,
                namespace=namespace
            )
            logger.info(f"Deleted {len(vector_ids)} vectors")
        except Exception as e:
            logger.error(f"Error deleting vectors: {e}")
            raise
    
    def delete_by_filter(
        self,
        filter_dict: Dict[str, Any],
        namespace: str
    ) -> None:
        """
        Delete vectors by metadata filter.
        
        Args:
            filter_dict: Metadata filter (e.g., {"doc_id": "..."})
            namespace: Namespace containing the vectors
        """
        logger.info(
            f"Deleting vectors from namespace '{namespace}' "
            f"with filter: {filter_dict}"
        )
        
        try:
            self.index.delete(
                filter=filter_dict,
                namespace=namespace
            )
            logger.info(f"Deleted vectors matching filter")
        except Exception as e:
            logger.error(f"Error deleting vectors by filter: {e}")
            raise
    
    def delete_namespace(self, namespace: str) -> None:
        """
        Delete all vectors in a namespace.
        
        Args:
            namespace: Namespace to delete
        """
        logger.info(f"Deleting all vectors in namespace '{namespace}'")
        
        try:
            self.index.delete(
                delete_all=True,
                namespace=namespace
            )
            logger.info(f"Deleted namespace '{namespace}'")
        except Exception as e:
            logger.error(f"Error deleting namespace: {e}")
            raise
    
    def similarity_search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        namespace: Optional[str] = None,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.
        
        Args:
            query_vector: Query vector
            top_k: Number of results to return
            namespace: Optional namespace to search in
            filter_dict: Optional metadata filter
            
        Returns:
            List of matches with id, score, and metadata
        """
        return self.query(
            vector=query_vector,
            namespace=namespace or "",
            top_k=top_k,
            filter_dict=filter_dict,
            include_metadata=True
        )
    
    def query(
        self,
        vector: List[float],
        namespace: str,
        top_k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Query vectors by similarity.
        
        Args:
            vector: Query vector
            namespace: Namespace to query
            top_k: Number of results to return
            filter_dict: Optional metadata filter
            include_metadata: Whether to include metadata
            
        Returns:
            List of matches with id, score, and metadata
        """
        try:
            response = self.index.query(
                vector=vector,
                namespace=namespace,
                top_k=top_k,
                filter=filter_dict,
                include_metadata=include_metadata
            )
            
            matches = []
            for match in response.matches:
                matches.append({
                    "id": match.id,
                    "score": match.score,
                    "metadata": match.metadata if include_metadata else {}
                })
            
            return matches
            
        except Exception as e:
            logger.error(f"Error querying vectors: {e}")
            raise
    
    def get_index_stats(self) -> Dict[str, Any]:
        """
        Get index statistics.
        
        Returns:
            Dict with index stats
        """
        try:
            stats = self.index.describe_index_stats()
            return {
                "dimension": stats.dimension,
                "total_vector_count": stats.total_vector_count,
                "namespaces": stats.namespaces
            }
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            raise

