import os
import json
import time
import argparse
from typing import List, Dict, Any

from embeddings.embedder import GeminiEmbedder
from rag.qdrant_service import QdrantService

def load_crop_knowledge(crop: str, base_dir: str) -> List[Dict[str, Any]]:
    """Loads knowledge records from data/processed/{crop}/{crop}_knowledge.jsonl"""
    file_path = os.path.join(base_dir, "data", "processed", crop, f"{crop}_knowledge.jsonl")
    records = []
    if not os.path.exists(file_path):
        print(f"[Warning] Knowledge file not found for crop '{crop}': {file_path}")
        return []
        
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if obj.get("content"):
                    records.append(obj)
            except Exception as e:
                print(f"Error parsing JSONL line: {e}")
                
    return records

def construct_embed_text(record: Dict[str, Any]) -> str:
    """
    Constructs a dense, semantically rich representation for the embedding model.
    Combines crop, topic, subtopic, disease/pest, and content.
    """
    crop = record.get("crop", "")
    topic = record.get("topic", "")
    subtopic = record.get("subtopic") or ""
    disease = record.get("disease") or ""
    pest = record.get("pest") or ""
    content = record.get("content", "")
    
    header_parts = [crop]
    if topic:
        header_parts.append(topic)
    if subtopic:
        header_parts.append(subtopic)
    if disease:
        header_parts.append(f"Disease: {disease}")
    if pest:
        header_parts.append(f"Pest: {pest}")
        
    header = " - ".join(header_parts)
    return f"{header}: {content}"

def ingest_crop_to_qdrant(crop: str, embedder: GeminiEmbedder, qdrant: QdrantService, base_dir: str, batch_size: int = 15):
    """
    Ingests all knowledge records for a single crop into Qdrant.
    """
    records = load_crop_knowledge(crop, base_dir)
    if not records:
        print(f"[{crop.upper()}] No records found. Skipping.")
        return 0

    print(f"\n==========================================")
    print(f"Ingesting {crop.upper()} ({len(records)} records)")
    print(f"==========================================")

    total_upserted = 0
    start_time = time.time()
    
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        embed_texts = [construct_embed_text(r) for r in batch]
        
        try:
            vectors = embedder.embed_texts(embed_texts, task_type="retrieval_document")
            count = qdrant.upsert_records(batch, vectors)
            total_upserted += count
            pct = (total_upserted / len(records)) * 100
            print(f"[{crop.capitalize()}] Batch {i//batch_size + 1}/{(len(records) + batch_size - 1)//batch_size}: Indexed {total_upserted}/{len(records)} records ({pct:.1f}%)")
        except Exception as e:
            print(f"[{crop.capitalize()}] Error in batch {i}-{i+batch_size}: {e}")
            raise e
            
        # Respect rate-limit safety pause
        time.sleep(0.5)

    elapsed = time.time() - start_time
    print(f"[{crop.upper()}] Ingestion complete! Upserted {total_upserted} records in {elapsed:.1f}s")
    return total_upserted

def main():
    parser = argparse.ArgumentParser(description="Ingest crop knowledge datasets into Qdrant vector database.")
    parser.add_argument("--crop", type=str, default="all", help="Crop to ingest: mango, coconut, sugarcane, tobacco, rice, or 'all'")
    parser.add_argument("--batch-size", type=int, default=15, help="Embedding batch size")
    args = parser.parse_args()

    # Paths: __file__ is in ai-service/ingestion/
    ingestion_dir = os.path.dirname(os.path.abspath(__file__))
    ai_service_dir = os.path.abspath(os.path.join(ingestion_dir, ".."))
    project_root = os.path.abspath(os.path.join(ai_service_dir, ".."))
    env_path = os.path.join(ai_service_dir, ".env")
    qdrant_storage = os.path.join(project_root, "data", "qdrant_storage")

    print(f"Project root: {project_root}")
    print(f"AI Service dir: {ai_service_dir}")
    print(f"Qdrant storage path: {qdrant_storage}")
    print(f"Env path: {env_path}")

    # Check remote QDRANT_URL vs local embedded storage
    from dotenv import load_dotenv
    load_dotenv(env_path)
    qdrant_url = os.getenv("QDRANT_URL")

    # Initialize Services
    embedder = GeminiEmbedder(env_path=env_path, output_dimensionality=768)
    qdrant = QdrantService(
        collection_name="agri_knowledge",
        vector_dim=768,
        storage_path=qdrant_storage if not qdrant_url or not qdrant_url.startswith("http") else None,
        url=qdrant_url if qdrant_url and qdrant_url.startswith("http") else None
    )

    all_crops = ["mango", "coconut", "sugarcane", "tobacco", "rice"]
    target_crops = all_crops if args.crop == "all" else [args.crop.lower()]

    total_records_ingested = 0
    for crop in target_crops:
        count = ingest_crop_to_qdrant(crop, embedder, qdrant, project_root, batch_size=args.batch_size)
        total_records_ingested += count

    print("\n" + "=" * 50)
    print(f"VECTOR DATABASE INGESTION SUMMARY")
    print("=" * 50)
    for crop in all_crops:
        crop_count = qdrant.count(crop=crop)
        print(f"  - {crop.capitalize():12s}: {crop_count:5d} vectors in collection")
    
    total_in_db = qdrant.count()
    print(f"\nTOTAL VECTORS IN 'agri_knowledge': {total_in_db}")
    print("=" * 50)
    qdrant.close()

if __name__ == "__main__":
    main()
