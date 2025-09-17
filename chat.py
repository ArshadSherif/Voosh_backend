import uuid
from redis_client import redis_client
import json
from google import genai
import os
from vector_store import search_articles
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("Missing GEMINI_API_KEY in environment")

client = genai.Client(api_key=api_key)

def create_session():
    """Creates a new chat session and initializes its history in Redis."""
    
    session_id = str(uuid.uuid4())
    #key : session:<session_id>:history ,  value : list of messages
    redis_client.set(f"session:{session_id}:history", json.dumps([]), ex=3600)
    return session_id

def fetch_session_history(session_id):
    """Retrieves the chat history for a given session from Redis."""
    history = redis_client.get(f"session:{session_id}:history")
    if history:
        return json.loads(history)
    return []


def generate_response(session_id: str, user_message: str):
    """Generates a response to the user's message and updates the session history."""
    
    result = search_articles(user_message, k=3)
    if not result:
        yield "Sorry I couldn't find any relevant articles."
        return 
    
    context = "\n\n".join(
        [f"Title: {r['title']}\nURL: {r['url']}\nSnippet: {r['text'][:500]}..." for r in result]
    )

    prompt = f"""
    You are a knowledgeable assistant specialized in news summaries. Use the context below to answer the user's question accurately.

    Context:
    {context}

    Instructions:
    - Only use information present in the context.
    - Provide a clear, concise answer in 2-4 sentences.
    - Include the title and URL of any source you reference in your answer.
    - If the answer cannot be found in the context, respond with: "I don't know based on the provided articles."

    Question:
    {user_message}

    Answer:
    """


    stream = client.models.generate_content_stream(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    
    for event in stream:
        if event.candidates:
            for part in event.candidates[0].content.parts:
                if part.text:
                    yield part.text


def add_message(session_id: str, role: str, content: str):
    key = f"session:{session_id}:history"
    history = redis_client.get(key)

    if history:
        history = json.loads(history)
    else:
        history = []

    history.append({"role": role, "content": content})
    redis_client.set(key, json.dumps(history), ex=3600)
