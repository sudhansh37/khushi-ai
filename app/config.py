"""Central configuration for Khushi AI.

Everything is controlled through environment variables (see .env.example),
so the same code runs on a laptop, in a GitHub Codespace, or in a container.
"""
import os

# --- Model -----------------------------------------------------------------
# Any GGUF model on the Hugging Face Hub works. Default is a small,
# CPU-friendly, multilingual (Hindi + English + Hinglish) instruct model.
MODEL_REPO = os.getenv("KHUSHI_MODEL_REPO", "Qwen/Qwen2.5-1.5B-Instruct-GGUF")
MODEL_FILE = os.getenv("KHUSHI_MODEL_FILE", "qwen2.5-1.5b-instruct-q4_k_m.gguf")
MODEL_CACHE = os.getenv("KHUSHI_MODEL_CACHE") or None

N_CTX = int(os.getenv("KHUSHI_N_CTX", "4096"))
N_THREADS = int(os.getenv("KHUSHI_N_THREADS", "0")) or None  # 0 -> auto
N_BATCH = int(os.getenv("KHUSHI_N_BATCH", "256"))

# --- Generation ------------------------------------------------------------
MAX_TOKENS = int(os.getenv("KHUSHI_MAX_TOKENS", "512"))
TEMPERATURE = float(os.getenv("KHUSHI_TEMPERATURE", "0.7"))
TOP_P = float(os.getenv("KHUSHI_TOP_P", "0.9"))

# --- Web research ----------------------------------------------------------
ENABLE_WEB = os.getenv("KHUSHI_ENABLE_WEB", "true").lower() in ("1", "true", "yes", "on")
WEB_MAX_RESULTS = int(os.getenv("KHUSHI_WEB_MAX_RESULTS", "5"))

# --- Server ----------------------------------------------------------------
HOST = os.getenv("KHUSHI_HOST", "0.0.0.0")
PORT = int(os.getenv("KHUSHI_PORT", "8000"))
