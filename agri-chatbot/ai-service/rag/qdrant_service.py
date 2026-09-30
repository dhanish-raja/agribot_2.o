import os
import json
import uuid
import hashlib
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    PayloadSchemaType
)

class QdrantService:
    """
    Manages Qdrant vector database operations:
    Supports both local embedded storage (path-based) and remote client (url-based).
    """
    def __init__(self, collection_name: str = "agri_knowledge", vector_dim: int = 768, storage_path: Optional[str] = None, url: Optional[str] = None):
        self.collection_name = collection_name
        self.vector_dim = vector_dim
        
        if url and url.startswith("http"):
            print(f"[QdrantService] Connecting to remote Qdrant at: {url}")
            self.client = QdrantClient(url=url)
        elif storage_path:
            os.makedirs(storage_path, exist_ok=True)
            print(f"[QdrantService] Initializing embedded local Qdrant at: {storage_path}")
            self.client = QdrantClient(path=storage_path)
        else:
            # Default to in-memory or default storage
            print("[QdrantService] Initializing in-memory Qdrant instance")
            self.client = QdrantClient(":memory:")
            
        self.ensure_collection()

    def ensure_collection(self):
        """Creates the collection if it doesn't already exist and builds payload indexes."""
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)
        
        if not exists:
            print(f"[QdrantService] Creating collection '{self.collection_name}' (dim={self.vector_dim}, distance=COSINE)...")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=self.vector_dim, distance=Distance.COSINE)
            )
            # Create payload indexes for fast filtering
            self._create_payload_indexes()
            print(f"[QdrantService] Collection '{self.collection_name}' ready.")
        else:
            print(f"[QdrantService] Collection '{self.collection_name}' already exists.")

    def _create_payload_indexes(self):
        """Indexes key categorical fields for fast filtering by crop, topic, disease, etc."""
        fields = ["crop", "topic", "subtopic", "disease", "pest", "organization"]
        for field in fields:
            try:
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name=field,
                    field_schema=PayloadSchemaType.KEYWORD
                )
            except Exception:
                pass

    def upsert_records(self, records: List[Dict[str, Any]], embeddings: List[List[float]]) -> int:
        """
        Upserts structured knowledge records with their corresponding dense vectors.
        Uses deterministic UUIDs based on content hash to ensure idempotent ingestion without duplicates.
        """
        if len(records) != len(embeddings):
            raise ValueError(f"Mismatch: {len(records)} records vs {len(embeddings)} embeddings")

        points = []
        for rec, vec in zip(records, embeddings):
            # Generate deterministic UUID from record content + crop + topic
            content_key = f"{rec.get('crop')}_{rec.get('topic')}_{rec.get('content')}"
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, content_key))
            
            payload = {
                "crop": rec.get("crop", "unknown"),
                "topic": rec.get("topic", "general"),
                "subtopic": rec.get("subtopic"),
                "information_type": rec.get("information_type"),
                "growth_stage": rec.get("growth_stage"),
                "disease": rec.get("disease"),
                "scientific_name": rec.get("scientific_name"),
                "pest": rec.get("pest"),
                "content": rec.get("content", ""),
                "source": rec.get("source"),
                "organization": rec.get("organization"),
                "source_url": rec.get("source_url"),
                "document_name": rec.get("document_name"),
                "section": rec.get("section"),
                "region": rec.get("region", "India"),
                "language": rec.get("language", "en")
            }
            
            points.append(PointStruct(id=point_id, vector=vec, payload=payload))

        # Batch upsert
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        return len(points)

    def search(self, query_vector: List[float], crop: Optional[str] = None, topic: Optional[str] = None, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Performs semantic vector search with optional metadata filtering.
        """
        filter_conditions = []
        if crop:
            filter_conditions.append(FieldCondition(key="crop", match=MatchValue(value=crop.lower())))
        if topic:
            filter_conditions.append(FieldCondition(key="topic", match=MatchValue(value=topic.lower())))

        query_filter = Filter(must=filter_conditions) if filter_conditions else None

        if hasattr(self.client, "query_points"):
            res = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                query_filter=query_filter,
                limit=top_k
            )
            results = res.points
        else:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=top_k
            )

        formatted = []
        for r in results:
            formatted.append({
                "id": r.id,
                "score": r.score,
                "payload": r.payload
            })
        return formatted

    def count(self, crop: Optional[str] = None) -> int:
        """Returns total records or filtered by crop."""
        query_filter = None
        if crop:
            query_filter = Filter(must=[FieldCondition(key="crop", match=MatchValue(value=crop.lower()))])
        return self.client.count(collection_name=self.collection_name, count_filter=query_filter).count

    def close(self):
        """Explicitly close client to avoid Python shutdown deallocator warning."""
        try:
            self.client.close()
        except Exception:
            pass
