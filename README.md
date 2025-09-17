# Voosh News RAG Chatbot Backend

This is the backend for a Retrieval-Augmented Generation (RAG) chatbot that answers user queries over a news corpus using Google Gemini and a vector database. Each user gets a unique session, with chat history stored in Redis.

---

## Tech Stack

- **Embeddings:** Jina Embeddings (or any open-source embedding model)
- **Vector DB:** Qdrant (or Chroma/faiss, configurable)
- **LLM API:** Google Gemini (via `google-genai`)
- **Backend:** Python (Flask/FastAPI, easily portable to Node.js/Express if needed)
- **Cache & Sessions:** Redis (in-memory)
- **Frontend:** [See frontend repo](#) (React + SCSS)

---

## Features

- **RAG Pipeline:**  
  - Ingests ~50 news articles (via RSS or scraping)
  - Embeds articles and stores in a vector DB
  - Retrieves top-k relevant articles for each query
  - Calls Gemini API for final answer, referencing sources

- **Session Management:**  
  - Each user gets a unique session ID
  - Chat history per session stored in Redis (TTL: 1 hour)
  - API endpoints to fetch and clear session history

- **Streaming Responses:**  
  - Gemini responses streamed to the frontend for a smooth UX

---

## Setup

### 1. Clone & Install

```bash
git clone https://github.com/yourusername/voosh-news-backend.git
cd voosh-news-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file:

```
GEMINI_API_KEY=your_google_gemini_api_key
REDIS_URL=redis://localhost:6379/0
VECTOR_DB_URL=http://localhost:6333  # Qdrant default
```

### 3. Run Redis & Vector DB

- **Redis:**  
  `sudo service redis-server start` (or use Docker)
- **Qdrant:**  
  `docker run -p 6333:6333 qdrant/qdrant`

### 4. Ingest News Articles

Use the provided script (e.g., `ingest.py`) to fetch, embed, and store news articles in the vector DB.

```bash
python ingest.py
```

### 5. Start the Backend

```bash
python app.py
```

---

## API Endpoints

- `POST /chat`  
  - Params: `session_id`, `user_message`
  - Returns: Streamed Gemini response

- `GET /session/<session_id>/history`  
  - Returns: Full chat history for the session

- `POST /session/<session_id>/clear`  
  - Clears chat history for the session

---

## Caching & Performance

- **Session History:**  
  - Stored in Redis with a TTL of 1 hour (`ex=3600` in code)
  - Example config in `chat.py`:
    ```python
    redis_client.set(f"session:{session_id}:history", json.dumps([]), ex=3600)
    ```
- **Cache Warming:**  
  - On server start, you can pre-load popular articles or FAQs into the vector DB for faster retrieval.

---

## End-to-End Flow

1. **User sends a message** (via frontend)
2. **Backend retrieves top-k articles** from vector DB using embeddings
3. **Gemini API** is called with context from retrieved articles
4. **Response is streamed** back to the frontend
5. **Chat history** is updated in Redis per session

---

## Design Decisions

- **RAG for factual accuracy:** Only information from retrieved articles is used in answers.
- **Redis for fast session management:** Ensures low-latency chat experience.
- **Streaming responses:** Improves UX by showing Gemini’s answer as it’s generated.
- **Modular vector DB:** Easily switch between Qdrant, Chroma, or faiss.

---

## Improvements

- Add persistent transcript storage in SQL (MySQL/Postgres)
- Enhance article ingestion (deduplication, scheduled updates)
- Add authentication for user sessions
- Deploy with Docker Compose for easy setup

---

## Demo

See the [frontend repo](#) for a full demo and video walkthrough.

---

## License

MIT

---

## Contact

For questions, email [richa@voosh.in](mailto:richa@voosh.in)