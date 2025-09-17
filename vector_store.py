from redis_client import redis_client
from sentence_transformers import SentenceTransformer
from redis.commands.search.field import TextField, VectorField
from redis.commands.search.index_definition import IndexDefinition, IndexType
import numpy as np
from redis.commands.search.query import Query


#config
EMBED_DIM = 384
model = SentenceTransformer("paraphrase-MiniLM-L3-v2")


def get_embedding(text:str):
    """Get the embedding for a given text."""
    emb = model.encode(text,normalize_embeddings=True)
    return emb

def create_redis_index():
    try:
        _= redis_client.ft("news_index").info()
        print("Index already exists")
    except:
        print("Creating Index")
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
                        "DIM": EMBED_DIM,
                        "DISTANCE_METRIC": "COSINE"
                    }
                )
            ],
            definition=IndexDefinition(prefix=["article:"], index_type=IndexType.HASH)
        )
        print("Created Redis Vector Index")
    
def store_articles_to_redis(articles):
    """
    Store fetched articles into Redis with embeddings.
    Each article is stored as a Redis HASH with prefix `article:`.
    """
    
    pipe = redis_client.pipeline()
    for i, article in enumerate(articles):
        emb = get_embedding(article["text"])
        emb_bytes = np.array(emb, dtype=np.float32).tobytes()
        
        key = f"article:{i}"
        pipe.hset(key,mapping={
            "title": article["title"],
            "text": article["text"],
            "url": article["url"],
            "embedding": emb_bytes
        })
    pipe.execute()
    print(f"✅ Stored {len(articles)} articles in Redis")

def search_articles(query: str, k: int = 5):
    # Embed the query
    query_emb = model.encode(query, normalize_embeddings=True)
    query_bytes = np.array(query_emb, dtype=np.float32).tobytes()

    # Build KNN query
    query_str = f'*=>[KNN {k} @embedding $vector AS score]'  # vector KNN search
    q = Query(query_str).sort_by("score").return_fields("title", "text", "url").paging(0, k)

    # Execute search
    res = redis_client.ft("news_index").search(q, query_params={"vector": query_bytes})

    #  Format results
    return [{"title": doc.title, "text": doc.text, "url": doc.url} for doc in res.docs]


