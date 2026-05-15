import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "data.json")

import redis.asyncio as redis

# ... keep your existing BASE_DIR and DB_FILE ...

# Redis Setup
REDIS_URL = "redisurl"
_redis_client = None

async def get_redis():
    global _redis_client
    if _redis_client is None:
        # decode_responses=True ensures we get strings, not bytes
        _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    return _redis_client

async def get_cached_prices():
    """
    Retrieves the JSON list of coin data from the 'market_prices' key.
    This follows the schema established in your backend ai.py.
    """
    try:
        r = await get_redis()
        data = await r.get("market_prices")
        return json.loads(data) if data else []
    except Exception as e:
        print(f"Redis fetch error: {e}")
        return []

# ... keep the rest of your JSON file functions (load_data, save_data, etc.) ...


def load_data():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "news": {"seen_links": [], "queue": []}}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_user(user_id):
    data = load_data()
    return data["users"].get(str(user_id))


def create_user(user_id):
    data = load_data()
    data["users"][str(user_id)] = {
        "language": None,
        "news_subscription": False
    }
    save_data(data)


def update_user(user_id, key, value):
    data = load_data()
    if str(user_id) not in data["users"]:
        create_user(user_id)
        data = load_data()
    data["users"][str(user_id)][key] = value
    save_data(data)


def get_all_users():
    return load_data()["users"]


def add_news_item(item):
    data = load_data()
    if item["link"] not in data["news"]["seen_links"]:
        data["news"]["seen_links"].append(item["link"])
        data["news"]["queue"].append(item)

        # limit queue
        if len(data["news"]["queue"]) > 100:
            data["news"]["queue"] = data["news"]["queue"][-100:]

        save_data(data)


def get_news_queue():
    return load_data()["news"]["queue"]


def pop_news_batch(n=3):
    data = load_data()
    batch = data["news"]["queue"][:n]
    data["news"]["queue"] = data["news"]["queue"][n:]
    save_data(data)
    return batch