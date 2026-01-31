import os
import sys
import time

# Set timeout env var just in case
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"

try:
    from huggingface_hub import snapshot_download
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("Dependencies missing. Please make sure requirements are installed.")
    sys.exit(1)

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
MAX_RETRIES = 5

def download_model():
    print(f"Attempting to download model: {MODEL_NAME}")
    
    for i in range(MAX_RETRIES):
        try:
            print(f"Attempt {i+1}/{MAX_RETRIES}...")
            # Try to download using snapshot_download first as it might be more robust
            path = snapshot_download(repo_id=MODEL_NAME)
            print(f"snapshot_download successful. Path: {path}")
            
            # Now verify checking via SentenceTransformer
            model = SentenceTransformer(MODEL_NAME)
            print("Successfully loaded SentenceTransformer!")
            return True
        except Exception as e:
            print(f"Error on attempt {i+1}: {e}")
            time.sleep(2)
            
    return False

if __name__ == "__main__":
    success = download_model()
    if success:
        print("Model downloaded and verified successfully.")
        sys.exit(0)
    else:
        print("Failed to download model after multiple attempts.")
        sys.exit(1)
