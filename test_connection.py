import redis

# Connect to the local Redis server on this machine
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

try:
    if r.ping():
        print("Success! Python is connected to Redis on Ubuntu.")
        r.set("test_greeting", "Hello from Ubuntu!")
        print("Redis returned:", r.get("test_greeting"))
except Exception as e:
    print("Connection error:", e)
