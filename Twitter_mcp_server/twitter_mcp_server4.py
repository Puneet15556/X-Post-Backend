import os
import sys
import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from tweepy import Client
import tweepy
from typing import Optional, Dict

# ---------------------------
# ✅ FORCE UTF-8 (Windows fix)
# ---------------------------
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

load_dotenv()

import time

# ---- CACHES ----
USER_ID_CACHE = {}
TIMELINE_CACHE = {}
CACHE_TTL = 60  # seconds


# ---------------------------
# 🔹 TOKENS (Fallback Defaults)
# ---------------------------
BEARER = os.getenv("TWITTER_BEARER_TOKEN")
API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

# ---------------------------
# 🔹 MCP SERVER
# ---------------------------
mcp = FastMCP("twitter-mcp")

# ---------------------------
# 🔍 SEARCH TWEETS (Bearer)
# ---------------------------
@mcp.tool()
async def search_tweets(query: str, limit: str = "5", credentials: Optional[Dict] = None):
    """
    Search recent public tweets. Optional credentials for user-specific keys.
    """
    
    user_bearer = (credentials or {}).get("bearer_token") or BEARER
    
    if not user_bearer:
        return {"error": "Missing Bearer Token"}

    query = query.strip()
    if not query or len(query) < 3:
        return {"error": "Search query must be at least 3 characters long."}

    try:
        limit = int(limit)
    except Exception:
        limit = 10

    limit = max(10, min(limit, 100))
    headers = {"Authorization": f"Bearer {user_bearer}"}

    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(
            "https://api.twitter.com/2/tweets/search/recent",
            headers=headers,
            params={
                "query": query,
                "max_results": limit,
                "tweet.fields": "created_at"
            }
        )

    r.raise_for_status()
    return r.json()


@mcp.tool()
async def get_user_tweets(username: str, limit: str = "5", credentials: Optional[Dict] = None):
    """
    Get recent tweets from a user's timeline. Optional credentials for user-specific keys.
    """
    user_bearer = (credentials or {}).get("bearer_token") or BEARER
    if not user_bearer:
        return {"error": "Missing Bearer Token"}

    username = username.strip().lstrip("@")
    if not username:
        return {"error": "Username is required."}

    try:
        limit = int(limit)
    except Exception:
        limit = 10

    limit = max(10, min(limit, 100))
    headers = {"Authorization": f"Bearer {user_bearer}"}

    async with httpx.AsyncClient(timeout=20) as client:
        if username not in USER_ID_CACHE:
            user_resp = await client.get(
                f"https://api.twitter.com/2/users/by/username/{username}",
                headers=headers,
            )
            user_resp.raise_for_status()
            user_json = user_resp.json()
            if "data" not in user_json:
                return {"error": f"User '{username}' not found or protected"}
            USER_ID_CACHE[username] = user_json["data"]["id"]

        user_id = USER_ID_CACHE[username]
        
        tweets_resp = await client.get(
            f"https://api.twitter.com/2/users/{user_id}/tweets",
            headers=headers,
            params={"max_results": limit, "tweet.fields": "created_at"}
        )
        tweets_resp.raise_for_status()
        return tweets_resp.json()


# ---------------------------
# ✍️ POST TWEET (Tweepy ✅)
# ---------------------------
@mcp.tool()
async def post_tweet(text: str, credentials: Optional[Dict] = None):
    """
    Post a tweet using provided or default credentials.
    """
    print("🔥🔥🔥 post_tweet EXECUTED 🔥🔥🔥")

    
    creds = credentials or {}
    try:
        current_client = Client(
            consumer_key=creds.get("api_key") or API_KEY,
            consumer_secret=creds.get("api_secret") or API_SECRET,
            access_token=creds.get("access_token") or ACCESS_TOKEN,
            access_token_secret=creds.get("access_token_secret") or ACCESS_SECRET,
        )

        response = current_client.create_tweet(text=text)
        return {"id": response.data["id"], "text": text}
        
    except tweepy.Forbidden:
        return {
            "status": "POST GENERATED BUT NOT SENT",
            "reason": "X API Free-tier does not allow posting. Use Paid Tier or check your keys.",
            "post": text
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    mcp.run(transport="stdio")