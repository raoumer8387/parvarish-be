"""Quick manual test: POST /api/v1/chat against running backend."""
import sys
from datetime import timedelta
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from app.core.security import create_access_token

BASE = "http://127.0.0.1:8000"
token = create_access_token({"sub": "1"}, expires_delta=timedelta(hours=1))
headers = {"Authorization": f"Bearer {token}"}

print("=== GET /api/v1/chat/history ===")
r_hist = httpx.get(f"{BASE}/api/v1/chat/history", params={"limit": 3}, headers=headers, timeout=30)
print("status:", r_hist.status_code)
print("body:", r_hist.text[:800])

print("\n=== POST /api/v1/chat ===")
r_chat = httpx.post(
    f"{BASE}/api/v1/chat",
    json={"message": "Assalamu alaikum. How can I teach patience to my child?"},
    headers=headers,
    timeout=300,
)
print("status:", r_chat.status_code)
print("body:", r_chat.text[:1500])
