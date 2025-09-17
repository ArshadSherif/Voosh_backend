from fastapi import FastAPI,Header,Body
from redis_client import redis_client
from fetch_news import fetch_news_from_rss
import json
from vector_store import create_redis_index, store_articles_to_redis, search_articles
from chat import create_session,generate_response,fetch_session_history,add_message
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost:8080",  # React dev server
    "https://voosh-frontend-azure.vercel.app",  # production
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    print("🚀 Starting background news fetch & embedding...")
    #fetch new and return articles
    articles = await fetch_news_from_rss() 
    # embed immediately after fetch
    await embed_articles(articles)  
    

async def embed_articles(articles):
    try:
        create_redis_index()
        store_articles_to_redis(articles)
        print(f"Embedded {len(articles)} articles on startup.")
    except Exception as e:
        print(f"Failed to embed articles: {e}")


@app.get("/")
async def root():
    return {"message": "backend running"}

#---------------------------------------------Testing endpoint to fetch news from redis

@app.get("/news")
async def get_news():
    cached_news = redis_client.get("news")
    if cached_news:
        return {"news": json.loads(cached_news)}
    return {"news": []}


        
@app.get("/query-news")
async def query_news(q: str, k: int = 5):
    if not q:
        return {"error": "Query string 'q' is required."}
    try:
        results = await search_articles(q, k)  
        return {"results": results}
    except Exception as e:
        return {"error": str(e)}
    

# -----------------------------------------------------Chat endpoints
@app.get("/session/history")
def get_session_history(_session_id: str=Header(None)):
    return {"history": fetch_session_history(_session_id)}

@app.post("/session/new")
def new_session():
    session_id = create_session()
    return {"session_id": session_id, "message": "New session created and set as default."}


@app.post("/session/chat/stream")
def chat_stream(_session_id: str = Header(...), body: dict = Body(...)):
    message = body.get("message")
    if not message:
        return {"error": "Message is required."}

    # Store user message
    add_message(_session_id, "user", message)

    # Stream AI reply (no storing yet, since reply comes in chunks)
    def stream_wrapper():
        collected = []
        for chunk in generate_response(_session_id, message):
            collected.append(chunk)
            yield chunk
        # After full response, store it in Redis history
        add_message(_session_id, "AI", "".join(collected))

    return StreamingResponse(stream_wrapper(), media_type="text/plain")


@app.get("/get-session-list")
def list_sessions():
    keys = redis_client.keys("session:*:history")
    sessions = []
    for key in keys:
        key_str = key.decode("utf-8") if isinstance(key, bytes) else key
        session_id = key_str.split(":")[1]

        history = fetch_session_history(session_id)
        sessions.append({
            "session_id": session_id,
            "last_message": history[-1]["content"] if history else "",
        })
    return {"sessions": sessions}



if __name__ == "__main__":
    import os, uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
