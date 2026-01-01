from typing import Literal

import json
import re

from typing import TypedDict, List , Annotated , Optional
from langgraph.graph import add_messages
from langgraph.types import interrupt
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import ToolException
from config import PROMPT , SYSTEM_PROMPT
from Twitter_mcp_server.client import create_client
from langchain_core.runnables import RunnableConfig  # 🔥 Added import
import json
import re
import os
from langchain_groq import ChatGroq


 
from utils import (
    llm_parse_entity,
    build_query_from_entity,
    extract_username,
)

# --------------------------------------------------
# STATE
# --------------------------------------------------
class State(TypedDict):
    chosen_tool: str
    tweet_topic: str
    input: str

    generated_post: Annotated[List[AIMessage], add_messages]
    human_feedback: Annotated[List[HumanMessage], add_messages]

    iteration: int
    max_iteration: int

    search_result: str
    
    search_tweet: str
    post_result: dict
    final_tweet : str
    
    error: Optional[str]
    error_type: Optional[str]
    trace: List[str]

    post_status: str
    post_id: str
    post: str
    reason: str
    
    


# --------------------------------------------------
# ROUTER
# --------------------------------------------------
async def tool_router_node(state: State , config: RunnableConfig):
    
    if state.get("iteration", 1) > 1:
        return {}
    
    user_input = state.get("input", "")
    if not user_input:
        return state  
    user_keys = config["configurable"].get("twitter_keys", {})
    groq_key = user_keys.get("groq_key")

    
    if groq_key:
        os.environ["GROQ_API_KEY"] = groq_key
        
    else:
        
        raise ValueError("No Groq API Key found! Please check the sidebar.")
    
    
    llm = ChatGroq(
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    max_tokens=300,
    groq_api_key=groq_key
)

    response = await llm.ainvoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_input),
    ])          

    tool = response.content.strip().lower()

    if tool not in {"search", "timeline", "post"}:
        raise ValueError("Invalid tool selected")

    state["chosen_tool"] = tool

    if tool == "post":
        state["tweet_topic"] = user_input
    elif tool =="input":
        llm_response = await llm.ainvoke(PROMPT + "\n" + user_input)
        print(llm_response.content)
            
    else:
        state["input"] =user_input
    return state


def decide_input(
    state,
) -> Literal["generate", "Call_Model_Search", "Call_Model_Timeline"]:
    chosen_tool = state.get("chosen_tool", "post")
    if chosen_tool == "post":
        return "generate"
    elif chosen_tool == "timeline":
        return "Call_Model_Timeline"
    elif chosen_tool == "search":
        return "Call_Model_Search"
    else:
        return "generate"  


# --------------------------------------------------
# POST GENERATION
# --------------------------------------------------
async def generate_post(state: State , config: RunnableConfig):
    prompt = f"""
Generate a creative and engaging X (Twitter) post (max 60 words).

Topic: {state.get('tweet_topic', '')}
Tone: friendly, engaging, concise.
Include hashtags if relevant.

AND PROVIDE ONLY THE POST.
""" 
    user_keys = config["configurable"].get("twitter_keys", {})
    groq_key = user_keys.get("groq_key")

    
    if groq_key:
        os.environ["GROQ_API_KEY"] = groq_key
    else:
        
        raise ValueError("No Groq API Key found! Please check the sidebar.")
    llm = ChatGroq(
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    max_tokens=300,
    groq_api_key=groq_key
)    
    
    response = await llm.ainvoke([HumanMessage(content=prompt)])

    return {
        "generated_post": [AIMessage(content=response.content)],
        "iteration": state.get("iteration", 1),
    }


# --------------------------------------------------
# HUMAN REVIEW
# --------------------------------------------------
async def wait_for_human(state):
    feedback = interrupt({
        "question": "Do you like this post? (type ok / good OR suggest refinement)",
        "post": state["generated_post"][-1].content,
        "iteration": state["iteration"],
    })
    
    state["human_feedback"].append(feedback)
    return state
    


def decide(state) -> Literal["accept", "refine"]:
    feedback_msg = state["human_feedback"][-1].content
    feedback = feedback_msg.lower().strip()

    if any(w in feedback for w in ["ok", "good"]):
        return "accept"

    if state.get("iteration", 0) >= state.get("max_iteration", 5):
        return "accept"

    return "refine"


# --------------------------------------------------
# REFINE
# --------------------------------------------------
async def refine_post(state: State , config: RunnableConfig):

    
    prompt = f"""
Improve the following tweet based on human feedback.

Tweet:
{state['generated_post'][-1].content}

Human feedback:
{state['human_feedback'][-1].content}

And provide ONLY THE IMPROVED POST WITH HASHTAGS IF RELEVANT.NOTHING ELSE.
""" 
    user_keys = config["configurable"].get("twitter_keys", {})
    groq_key = user_keys.get("groq_key")

    
    if groq_key:
        os.environ["GROQ_API_KEY"] = groq_key
    else:
        
        raise ValueError("No Groq API Key found! Please check the sidebar.")
    
    llm = ChatGroq(
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    max_tokens=300,
    groq_api_key=groq_key
)    
    response = await llm.ainvoke([HumanMessage(content=prompt)])

    return {
        "generated_post": [AIMessage(content=response.content)],
        "iteration": state["iteration"] + 1,
    }


# --------------------------------------------------
# ACCEPT
# --------------------------------------------------
async def accept_post(state):
    print("\n✅ FINAL APPROVED TWEET:\n")
    print(state["generated_post"][-1].content)
    return {"final_tweet": state["generated_post"][-1].content}



# --------------------------------------------------
# SEARCH (MCP)
# --------------------------------------------------
async def call_model_search(state, config: RunnableConfig): # 🔥 Added config
    # 🔑 Get keys from config
    user_keys = config["configurable"].get("twitter_keys", {})
    groq_key = user_keys.get("groq_key")

    
    if groq_key:
        os.environ["GROQ_API_KEY"] = groq_key
    else:
        
        raise ValueError("No Groq API Key found! Please check the sidebar.")

    mcp_client = await create_client()
    tools = await mcp_client.get_tools()
    tool_map = {t.name: t for t in tools}
    
    llm = ChatGroq(
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    max_tokens=300,
    groq_api_key=groq_key
)

    
    entity_data = await llm_parse_entity(llm, state["input"])

    
    query = build_query_from_entity(entity_data)

    print("\n🧠 ENTITY DATA:", entity_data)
    print("🔎 TWITTER QUERY:", query)

    try:
        result = await tool_map["search_tweets"].ainvoke({
            "query": query,
            "limit": "10",
            "credentials": user_keys  
        })

        tweets = result.get("data", [])

        clean = []
        for t in tweets:
            text = t["text"]
            if text.startswith("RT @"):
                continue
            text = re.sub(r"http\S+", "", text).strip()
            clean.append({
                "id": t["id"],
                "text": text,
                "created_at": t["created_at"],
            })
        

        
        clean_result = llm.invoke(f"Give me JUST THE ORIGINAL READABLE TEXT FORMAT OF THE FOLLOWING TWEETS IN A ORIGINAL FORMAT: {clean}. DO NOT PROVIDE ANYTHING ELSE JUST THE READABLE TEXT.")
        return {
            "search_result": clean_result.content
        }
     
    except ToolException as e:
        if "429" in str(e):
            print("⚠️ X API rate limit hit (search). Skipping search.")
            return {"search_tweet": "NO TWEET"}
        else:
            raise    

# --------------------------------------------------
# TIMELINE (MCP)
# --------------------------------------------------
async def call_model_timeline(state, config: RunnableConfig): 
    user_keys = config["configurable"].get("twitter_keys")
    from langchain_core.tools import ToolException
    try:
        mcp_client = await create_client()
        tools = await mcp_client.get_tools()
        tool_map = {t.name: t for t in tools}

        username = extract_username(state["input"])
        if not username:
            raise ValueError("Could not extract Twitter username")

        raw_result = await tool_map["get_user_tweets"].ainvoke({
            "username": username,
            "limit": "20",
            "credentials": user_keys 
        })

        if isinstance(raw_result, list):
            raw_text = raw_result[0]["text"]
            result = json.loads(raw_text)
        else:
            result = raw_result
    except ToolException as e:
        return {
        "search_result": [],
        "error": str(e),
        "error_type": "RATE_LIMIT",
        "trace": [f"Timeline error (get_user_tweets): {str(e)}"],
    }

    if isinstance(result, dict) and "error" in result:
        return {
            "search_result": [],
            "error": result["error"],
            "error_type": "MCP_ERROR",
            "trace": [f"Timeline error (MCP): {result['error']}"],
        }

    tweets = result.get("data", [])
    if not tweets:
        return {"search_result": []}

    latest = tweets[0]
    clean_text = re.sub(r"http\S+", "", latest["text"]).strip()

    output = {
        "account": username,
        "tweet_id": latest["id"],
        "text": clean_text,
        "created_at": latest["created_at"]
    }

    print(f"\n🧾 LATEST TWEET BY @{username}")
    print(clean_text)
    print("🕒", latest["created_at"])

    return {"search_result": output}

# --------------------------------------------------
# POST TO TWITTER (MCP)
# --------------------------------------------------
async def call_model_post(state, config: RunnableConfig): 
    user_keys = config["configurable"].get("twitter_keys") 
    print("🔥 call_model_post ENTERED")

    mcp_client = await create_client()
    tools = await mcp_client.get_tools()
    tool_map = {t.name: t for t in tools}

    tweet = None
    if state.get("generated_post"):
        tweet = state["generated_post"][-1].content
    elif state.get("final_tweet"):
        tweet = state["final_tweet"]
    else:
        raise RuntimeError("No tweet content available")

    print("🔥 post_tweet WILL BE CALLED")

    
    result = await tool_map["post_tweet"].ainvoke({
        "text": tweet,
        "credentials": user_keys 
    })

    print("🚀 POST RESULT:", result)

    payload = json.loads(result[0]["text"])    
    print(f"PAYLOAD: {payload}")

    if payload.get("id"):
        state["post_status"] = "POST SENT"
        state["post_id"] = payload["id"]
        state["post"] = payload["text"]
    elif payload.get("error"):
        state["post_status"] = "POST GENERATED BUT NOT SENT"   
        state["reason"] = payload["error"] + " : X API Free-tier do not allowed post your tweet. Try again after some time or use Paid Tier (PAID API)"
        state["post"] = tweet

    return state