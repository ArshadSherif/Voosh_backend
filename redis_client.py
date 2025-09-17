import redis

# Connect to Redis (default localhost:6379)
redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
