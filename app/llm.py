"""Local, CPU-only LLM wrapper around llama.cpp (no GPU, no cloud)."""
import os

from huggingface_hub import hf_hub_download, list_repo_files
from llama_cpp import Llama


def ensure_model(repo_id, filename, cache_dir=None):
    """Download the GGUF file if needed and return its local path.

    Falls back to auto-picking a Q4_K_M quant if the exact filename is missing.
    """
    try:
        return hf_hub_download(repo_id=repo_id, filename=filename, cache_dir=cache_dir)
    except Exception:
        files = list_repo_files(repo_id)
        ggufs = [f for f in files if f.lower().endswith(".gguf")]
        pick = next((f for f in ggufs if "q4_k_m" in f.lower()), ggufs[0] if ggufs else None)
        if not pick:
            raise RuntimeError(f"No .gguf file found in Hugging Face repo: {repo_id}")
        return hf_hub_download(repo_id=repo_id, filename=pick, cache_dir=cache_dir)


class KhushiLLM:
    def __init__(self, model_path, n_ctx=4096, n_threads=None, n_batch=256):
        if n_threads is None:
            n_threads = max(1, os.cpu_count() or 2)
        self.llm = Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            n_threads=n_threads,
            n_batch=n_batch,
            verbose=False,
        )

    def complete(self, messages, max_tokens=512, temperature=0.7, top_p=0.9):
        out = self.llm.create_chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
        )
        return out["choices"][0]["message"]["content"]

    def stream(self, messages, max_tokens=512, temperature=0.7, top_p=0.9):
        for chunk in self.llm.create_chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stream=True,
        ):
            piece = chunk["choices"][0].get("delta", {}).get("content")
            if piece:
                yield piece
