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
        
        # Step 3: Load data if needed
        if count == 0:
            print("Step 3: Loading Islamic knowledge from data files...")
            data_loader = DataLoader()
            docs = data_loader.load()
            print(f"✅ Loaded {len(docs)} documents from data files\n")
            
            print("Step 4: Building index...")
            embedder.build_index(docs)
            print(f"✅ Indexed {len(docs)} documents into vector store\n")
            
            # Verify
            new_count = collection.count()
            print(f"✅ Verified: Collection now has {new_count} documents\n")
        else:
            print(f"✅ Collection already has {count} documents, skipping load\n")
        
        # Step 5: Test retrieval
        print("Step 5: Testing retrieval...")
        retriever = Retriever(collection)
        
        test_queries = [
            "focus attention mindfulness",
            "emotions patience forgiveness",
            "seeking knowledge learning",
            "good character akhlaq morality"
        ]
        
        for query in test_queries:
            print(f"\n  Query: '{query}'")
            chunks = retriever.query(query, k=2)
            print(f"  Found {len(chunks)} results:")
            for i, chunk in enumerate(chunks, 1):
                preview = chunk.text[:100].replace('\n', ' ')
                print(f"    {i}. {preview}...")
        
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
