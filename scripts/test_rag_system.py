"""Script to pre-load and test RAG embeddings.

Run this before starting the server to ensure RAG system works properly.
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.rag.embedder import Embedder
from app.rag.data_loader import DataLoader
from app.rag.retriever import Retriever

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_rag_system():
    """Test the RAG system end-to-end."""
    
    print("\n" + "="*70)
    print("RAG SYSTEM TEST - Islamic Knowledge Base")
    print("="*70 + "\n")
    
    try:
        # Step 1: Initialize embedder
        print("Step 1: Initializing embedder...")
        embedder = Embedder()
        print("✅ Embedder initialized successfully\n")
        
        # Step 2: Check collection
        collection = embedder.as_retriever()
        count = collection.count()
        print(f"Step 2: Current collection has {count} documents\n")
        
        # Step 3: Load data and sync index
        print("Step 3: Loading Islamic knowledge from data files...")
        data_loader = DataLoader()
        docs = data_loader.load()
        print(f"✅ Loaded {len(docs)} documents from data files\n")

        print("Step 4: Syncing vector index...")
        rebuilt = embedder.ensure_index(docs, data_signature=data_loader.source_signature())
        if rebuilt:
            print(f"✅ Rebuilt index with {len(docs)} documents\n")
        else:
            print(f"✅ Index already up to date ({embedder.collection.count()} documents)\n")

        new_count = collection.count()
        print(f"✅ Verified: Collection has {new_count} documents\n")
        
        # Step 5: Test retrieval
        print("Step 5: Testing retrieval...")
        retriever = Retriever(collection)
        
        test_queries = [
            "hadith anger control active child behavior",
            "quran verse patience mercy parenting",
            "focus attention mindfulness",
            "emotions patience forgiveness",
        ]
        
        for query in test_queries:
            print(f"\n  Query: '{query}'")
            chunks = retriever.retrieve_parenting_context(query, k=5)
            print(f"  Found {len(chunks)} results:")
            for i, chunk in enumerate(chunks, 1):
                ctype = retriever._content_type(chunk)
                preview = chunk.text[:100].replace('\n', ' ')
                print(f"    {i}. [{ctype}] {preview}...")
        
        print("\n" + "="*70)
        print("✅ RAG SYSTEM TEST PASSED!")
        print("="*70 + "\n")
        
        return True
        
    except Exception as e:
        print("\n" + "="*70)
        print("❌ RAG SYSTEM TEST FAILED!")
        print("="*70)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_rag_system()
    sys.exit(0 if success else 1)
