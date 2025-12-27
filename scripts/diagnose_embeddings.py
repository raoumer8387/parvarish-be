"""Quick diagnostic script for embedding model issues."""

import sys

print("\n" + "="*70)
print("EMBEDDING MODEL DIAGNOSTIC")
print("="*70 + "\n")

# Test 1: Check PyTorch
print("Test 1: PyTorch...")
try:
    import torch
    print(f"✅ PyTorch version: {torch.__version__}")
    print(f"   CUDA available: {torch.cuda.is_available()}")
    print(f"   Default device: cpu (forced)")
except ImportError as e:
    print(f"❌ PyTorch not installed: {e}")
    sys.exit(1)

# Test 2: Check SentenceTransformers
print("\nTest 2: SentenceTransformers...")
try:
    from sentence_transformers import SentenceTransformer
    print(f"✅ SentenceTransformers imported successfully")
except ImportError as e:
    print(f"❌ SentenceTransformers not installed: {e}")
    print("   Run: pip install sentence-transformers")
    sys.exit(1)

# Test 3: Load model
print("\nTest 3: Loading embedding model...")
try:
    model_name = "all-MiniLM-L6-v2"
    print(f"   Model: {model_name}")
    print(f"   Device: cpu (forced to avoid GPU issues)")
    
    model = SentenceTransformer(model_name, device='cpu')
    print(f"✅ Model loaded successfully")
    
    # Test encoding
    test_text = "This is a test sentence"
    embedding = model.encode(test_text)
    print(f"✅ Test encoding successful (dimension: {len(embedding)})")
    
except Exception as e:
    print(f"❌ Model loading failed: {e}")
    print("\n   Possible fixes:")
    print("   1. pip install --upgrade torch sentence-transformers")
    print("   2. pip install torch==2.0.1 sentence-transformers==2.2.2")
    print("   3. Clear cache: rm -rf ~/.cache/torch/sentence_transformers/")
    sys.exit(1)

# Test 4: Check ChromaDB
print("\nTest 4: ChromaDB...")
try:
    import chromadb
    print(f"✅ ChromaDB imported successfully")
    
    from chromadb.utils import embedding_functions
    print(f"✅ ChromaDB embedding functions available")
    
    # Test embedding function
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2",
        device='cpu'
    )
    print(f"✅ ChromaDB embedding function created")
    
except TypeError:
    # Older version might not support device parameter
    print(f"⚠️  ChromaDB version might not support device parameter")
    try:
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        print(f"✅ ChromaDB embedding function created (without device param)")
    except Exception as e2:
        print(f"❌ Failed: {e2}")
        sys.exit(1)
except Exception as e:
    print(f"❌ ChromaDB error: {e}")
    sys.exit(1)

print("\n" + "="*70)
print("✅ ALL DIAGNOSTIC TESTS PASSED!")
print("="*70)
print("\nYour embedding setup is ready. You can now:")
print("1. Run: python scripts/test_rag_system.py")
print("2. Start the server: uvicorn main:app --reload")
print("\n")
