import google.generativeai as genai
import os
import time

from redis_client import redis_client
# No longer need sentence_transformers
from redis.commands.search.field import TextField, VectorField
from redis.commands.search.index_definition import IndexDefinition, IndexType
import numpy as np
from redis.commands.search.query import Query


genai.configure(api_key=os.environ["GEMINI_API_KEY"])


EMBED_DIM = 768
EMBEDDING_MODEL = "models/text-embedding-004"

def create_redis_index():
    """Create a Redis search index with the correct embedding dimension."""
    try:
        # Check if index exists
        redis_client.ft("news_index").info()
        print("Index already exists")
    except Exception:
        print("Creating Index")
        # Create the index
        redis_client.ft("news_index").create_index(
            fields=[
                TextField("title"),
                TextField("text"),
                TextField("url"),
                VectorField(
                    "embedding",
                    "FLAT",
                    {
                        "TYPE": "FLOAT32",
                        "DIM": EMBED_DIM, # Updated Dimension
                        "DISTANCE_METRIC": "COSINE"
                    }
                )
            ],
            definition=IndexDefinition(prefix=["article:"], index_type=IndexType.HASH)
        )
        print("Created Redis Vector Index")

def store_articles_to_redis(articles):
    """
    Get embeddings from Gemini API in batches and store articles in Redis.
    """
    # Gemini API has a limit on requests per minute. Batching and sleeping helps avoid this.
    # The API also has a limit on how many texts can be in one request (e.g., 100).
    BATCH_SIZE = 50 # Batch size for both API calls and Redis pipeline
    
    for i in range(0, len(articles), BATCH_SIZE):
        batch_articles = articles[i:i+BATCH_SIZE]
        texts_to_embed = [article["text"] for article in batch_articles]

        # --- Gemini API Call ---
        # Make a single API call for the entire batch.
        # Use "retrieval_document" for texts that will be stored and searched.
        result = genai.embed_content(
            model=EMBEDDING_MODEL,
            content=texts_to_embed,
            task_type="retrieval_document"
        )
        embeddings = result['embedding']
        
        # --- Redis Pipeline ---
        pipe = redis_client.pipeline()
        for j, article in enumerate(batch_articles):
            emb = embeddings[j]
            # Use float32 to match the index definition
            emb_bytes = np.array(emb, dtype=np.float32).tobytes()

            key = f"article:{i+j}"
            pipe.hset(key, mapping={
                "title": article["title"],
                "text": article["text"],
                "url": article["url"],
                "embedding": emb_bytes
            })
        pipe.execute()
        
        print(f"Stored batch {i//BATCH_SIZE + 1}/{(len(articles) + BATCH_SIZE - 1)//BATCH_SIZE}")

        # --- Rate Limiting ---
        # Sleep for 1 second after each batch to stay under 60 requests/minute
        time.sleep(1)

    print(f"✅ Stored {len(articles)} articles in Redis")

def search_articles(query: str, k: int = 5):
    """Embed the search query using Gemini and perform a vector search in Redis."""
    
    # --- Gemini API Call ---
    # Use "retrieval_query" for the search query embedding
    result = genai.embed_content(
        model=EMBEDDING_MODEL,
        content=query,
        task_type="retrieval_query"
    )
    query_emb = result['embedding']
    query_bytes = np.array(query_emb, dtype=np.float32).tobytes()

    # --- Redis Search Query ---
    query_str = f'*=>[KNN {k} @embedding $vector AS score]'
    q = Query(query_str).sort_by("score").return_fields("title", "text", "url", "score").dialect(2)

    # Execute search
    res = redis_client.ft("news_index").search(q, query_params={"vector": query_bytes})

    # Format results
    return [{"title": doc.title, "text": doc.text, "url": doc.url, "score": doc.score} for doc in res.docs]