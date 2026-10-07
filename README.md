# 🌸 Khushi AI

**A small, fully-local, open-source chatbot that runs on CPU — no GPU, no cloud, no API key.**

Khushi speaks **Hindi, English and Hinglish**, has a warm and engaging personality,
and can **search the web** (via DuckDuckGo, key-free) to answer with fresh information.
It ships with a built-in chat UI *and* an **OpenAI-compatible API**, so you can plug it
into **any frontend** you like.

---

## 📱 Use it on your phone (no install, no server)

**Open: <https://sudhansh37.github.io/khushi-ai/>**

This is the in-browser build. The model runs **on your device** with WebGPU
(via WebLLM) — no server, no API key, nothing to install. Just open the URL,
tap **Load model** once (~1 GB, downloaded once and cached), and chat.

- Works on modern Android Chrome / Edge and iOS Safari 18+ (WebGPU required).
- 🔎 **Research** toggle pulls context from Wikipedia + DuckDuckGo directly in
  the browser (both allow CORS), so it works with no backend.
- The page is served by GitHub Pages from the [`docs/`](docs/) folder.

---

## Why it's free to run

- **Model:** a small quantized GGUF model (default ~1 GB) that runs on plain CPU via `llama.cpp`.
- **Inference:** `llama-cpp-python` — pure CPU, no GPU needed.
- **Research:** DuckDuckGo search — no API key.
- **Hosting:** runs happily in a **GitHub Codespace** free tier (a `.devcontainer` is included),
  or on your own laptop, or in the included Docker image.

> On CPU expect roughly a few tokens per second for a 1.5B model. It's not ChatGPT-fast,
> but it's private, offline-capable and costs nothing.

---

## Quick start

### Option A — GitHub Codespaces (recommended, zero setup)

1. Open this repo on GitHub → **Code ▸ Codespaces ▸ Create codespace on main**.
2. Wait for `pip install -r requirements.txt` to finish (the devcontainer does it for you).
3. In the Codespaces terminal:

   ```bash
   python run.py
   ```

4. Open the forwarded **port 8000** — the chat UI appears. First run downloads the model once.

### Option B — Your own machine (Linux / macOS / Windows)

```bash
git clone https://github.com/<your-username>/khushi-ai.git
cd khushi-ai

python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env        # optional — tweak model / settings
python run.py
```

Then open <http://localhost:8000>.

### Option C — Docker

```bash
docker build -t khushi-ai .
docker run -p 8000:8000 khushi-ai
```

---

## Choosing a model

Khushi works with **any GGUF model** on the Hugging Face Hub. Set it in `.env`:

| Use case | `KHUSHI_MODEL_REPO` | `KHUSHI_MODEL_FILE` |
|---|---|---|
| Default (fast, multilingual) | `Qwen/Qwen2.5-1.5B-Instruct-GGUF` | `qwen2.5-1.5b-instruct-q4_k_m.gguf` |
| Hindi / Hinglish native (1.7B, ~1 GB) | `eulogik/Bharat-Tiny-LLM-v3` | `bharat-tiny-llm-v3-q4_k_m.gguf` |
| Bigger / smarter (slower on CPU) | `Qwen/Qwen2.5-3B-Instruct-GGUF` | `qwen2.5-3b-instruct-q4_k_m.gguf` |

If the exact filename is wrong, Khushi auto-picks a `Q4_K_M` quant from the repo.
Pick a smaller quant (Q4_K_M / Q4_K_S) if RAM is tight; a bigger one (Q5/Q6) for better quality.

---

## Using it from **any** frontend

Khushi exposes three ways to talk to it. CORS is open, so a website or app can call it directly.

### 1. Simple JSON — `POST /chat`

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Bharat ki rajdhani kya hai?","history":[],"use_web":true}'
```

```json
{ "reply": "Bharat ki rajdhani New Delhi hai.", "sources": [ {"title":"…","url":"…"} ] }
```

### 2. Streaming — `POST /chat/stream`

Streams plain text. The first line is a JSON header with `sources`, then a `---`
separator, then the answer tokens. (This is what the built-in UI uses.)

### 3. OpenAI-compatible — `POST /v1/chat/completions`

Drop-in for any OpenAI SDK or frontend (Open WebUI, LibreChat, Chatbox, your own app…).
Just point the base URL at Khushi:

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="not-needed")
r = client.chat.completions.create(
    model="khushi",
    messages=[{"role": "user", "content": "Hi Khushi, kaise ho?"}],
)
print(r.choices[0].message.content)
```

```js
// JavaScript
const res = await fetch("http://localhost:8000/v1/chat/completions", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ model: "khushi", messages: [{ role: "user", content: "Hello!" }] }),
});
const data = await res.json();
console.log(data.choices[0].message.content);
```

---

## Configuration

Copy `.env.example` to `.env` and edit. Key variables:

| Variable | Default | What it does |
|---|---|---|
| `KHUSHI_MODEL_REPO` | `Qwen/Qwen2.5-1.5B-Instruct-GGUF` | Hugging Face repo of the GGUF model |
| `KHUSHI_MODEL_FILE` | `qwen2.5-1.5b-instruct-q4_k_m.gguf` | GGUF filename inside that repo |
| `KHUSHI_N_CTX` | `4096` | Context window (tokens) |
| `KHUSHI_N_THREADS` | `0` (auto) | CPU threads to use |
| `KHUSHI_MAX_TOKENS` | `512` | Max reply length |
| `KHUSHI_TEMPERATURE` | `0.7` | Creativity |
| `KHUSHI_ENABLE_WEB` | `true` | Turn web research on/off |
| `KHUSHI_WEB_MAX_RESULTS` | `5` | Search results used per query |
| `KHUSHI_HOST` / `KHUSHI_PORT` | `0.0.0.0` / `8000` | Bind address |

---

## Project layout

```
khushi-ai/
├── app/
│   ├── main.py       # FastAPI server + all endpoints
│   ├── llm.py        # CPU model loading + streaming (llama.cpp)
│   ├── search.py     # DuckDuckGo web research (no API key)
│   ├── persona.py    # Khushi's personality + language rules
│   └── config.py     # env-var configuration
├── static/index.html # built-in chat UI
├── run.py            # start the server
├── requirements.txt
├── Dockerfile
└── .devcontainer/    # one-click GitHub Codespaces setup
```

---

## How the language + research behaviour works

- **Language:** the system prompt tells Khushi to reply in the *same language and script*
  the user writes in — Devanagari Hindi, Roman Hinglish, or English — so you never have to
  switch modes manually.
- **Research:** when web research is on, Khushi searches DuckDuckGo, feeds the top results
  into the prompt as context, and is instructed to cite the source and never to claim it
  browsed pages it wasn't given. Toggle it off in the UI or send `"use_web": false`.

---

## Notes & limitations

- Small CPU models can hallucinate — treat answers as a helpful draft, not gospel.
- CPU inference is modest; use `KHUSHI_N_THREADS` to match your machine and a smaller
  quant if replies feel slow.
- Web research depends on DuckDuckGo being reachable; if it's blocked, the bot still
  answers from general knowledge.

## 🤖 Using Khushi as a research tool for your own agent

Use the **server** version (not the in-browser one) for agents. Deploy it on any
cloud host and your agent gets two useful endpoints:

**Research only** — no LLM reply, just retrieval + a ready context block:

```bash
curl -X POST https://your-host/research \
  -H "Content-Type: application/json" \
  -d '{"query":"latest ISRO missions","max_results":5}'
```

```json
{ "query": "…",
  "results":  [{"title":"…","url":"…","snippet":"…"}],
  "sources":  [{"title":"…","url":"…"}],
  "context":  "[1] … — …\n…" }
```

**Full answer with research baked in** — OpenAI-compatible, so most agent
frameworks can call it as a normal model:

```python
from openai import OpenAI
client = OpenAI(base_url="https://your-host/v1", api_key="not-needed")
```

Notes for cloud use:

- GitHub Pages **cannot** host the server (it is static only). Use Render,
  Railway, Fly.io, Hugging Face Spaces or a VPS — anything that runs a
  long-lived process.
- DuckDuckGo can rate-limit datacenter IPs, so research falls back to the
  Wikipedia API automatically. Swap in a proper search backend in
  `app/search.py` if you need more.

## License

MIT — see [LICENSE](LICENSE). Built on the shoulders of `llama.cpp`, `llama-cpp-python`,
Hugging Face, FastAPI and DuckDuckGo. Model weights keep their own licenses.
