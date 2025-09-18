# News RAG Chatbot Backend

A Retrieval-Augmented Generation (RAG) chatbot that provides news-based answers using vector similarity search and Google Gemini. Features session management and streaming responses.

## Tech Stack

- **Embeddings:** 
  - Local: Sentence Transformers (`paraphrase-albert-small-v2`)
  - Deployed: Google Gemini Embeddings API 
- **Vector Storage:** Redis with Vector Search
- **LLM:** Google Gemini
- **Backend:** Python (FastAPI)
- **Cache & Sessions:** Redis
- **Frontend:** React + tailwind

## Implementation Notes

### Local vs Deployed Version
- **Local Development:**
  - Uses `sentence-transformers` for embeddings
  - Higher quality embeddings but requires ~1GB memory
  - Ideal for development and demos

- **Production Deployment:**
  - Uses Gemini API for embeddings
  - Optimized for <512MB memory ( due to free-tier hosting)
  - Trades memory efficiency for embedding quality

## Features

- **RAG Pipeline:**
  - News ingestion via RSS feeds
  - Vector similarity search
  - Context-aware responses using Gemini
  - Source attribution

- **Session Management:**
  - Unique session IDs
  - Redis-backed chat history (30 mins TTL)
  - History retrieval/New Session apis

- **Streaming:**
  - Real-time response streaming
  - Progressive UI updates

## Setup

### Prerequisites
```bash
sudo apt update
sudo apt install redis-server python3-venv
```

### Installation
```bash
git clone https://github.com/yourusername/voosh-news-backend
cd voosh-news-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configuration
Create `.env`:
```
GEMINI_API_KEY=your_key_here
REDIS_URL=redis://localhost:6379/0
```

### Running
```bash
# Start Redis
sudo service redis-server start

# Start backend
fastapi dev main.py
```

## API Endpoints

### Chat
```
POST /chat
Body: {
  "session_id": "string",
  "message": "string"
}
```

### Session Management
```
GET /session/{session_id}/history
POST /session/{session_id}/clear
```

## Planned Improvements

### Infrastructure
- **Dedicated Vector Database:**
  - Migration to Pinecone/Weaviate
  - Improved scaling and search capabilities

- **Background Processing:**
  - Async embedding generation
  - Scheduled news updates

- **User Experience:**
  - OAuth2 authentication
  - History exports
  - API key management

### Performance

- **Scalability:**
  - Load balancing
  - Rate limiting

### DevOps
- **Containerization:**
  - Docker Compose setup
  - Kubernetes deployment
  - Auto-scaling configs

- **Monitoring:**
  - Prometheus metrics
  - Grafana dashboards
  - Error tracking
  - Performance monitoring

