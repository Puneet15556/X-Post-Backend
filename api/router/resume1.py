import json
from fastapi import APIRouter, Header, HTTPException
from typing import Optional

from langchain_core.messages import HumanMessage
from langgraph.types import Command

from api.schemas import ResumeRequest
from graph.workflow import build_graph


workflow = build_graph()

router = APIRouter(tags=["Resume"])

@router.post("/resume/{thread_id}")
async def resume(
    thread_id :str, 
    req: ResumeRequest,
    
    x_twitter_bearer: Optional[str] = Header(None),
    x_twitter_api_key: Optional[str] = Header(None),
    x_twitter_api_secret: Optional[str] = Header(None),
    x_twitter_access_token: Optional[str] = Header(None),
    x_twitter_access_secret: Optional[str] = Header(None),
    x_groq_api_key: Optional[str] = Header(None)
):
    """
    Resume execution from a LangGraph interrupt
    and send feedback using the provided API keys
    """

    
    config = {
        "configurable": {
            "thread_id": thread_id,
            "twitter_keys": {
                "bearer_token": x_twitter_bearer,
                "api_key": x_twitter_api_key,
                "api_secret": x_twitter_api_secret,
                "access_token": x_twitter_access_token,
                "access_token_secret": x_twitter_access_secret,
                "groq_key": x_groq_api_key
            }
        }
    }
    
    try:

        result = await workflow.ainvoke(
            Command(resume=HumanMessage(content=req.feedback)),
            config=config
        )
        
        state = workflow.get_state(config)
        values = state.values     
        
        if not result:
            return {
                "status": "ERROR",
                "reason": "Workflow returned no result",
            }

        
        if "__interrupt__" in result:
            interrupt_data = result["__interrupt__"][0].value
            if interrupt_data.get("error"):
                return {
                    "status": "ERROR",
                    "reason": interrupt_data.get("error"),
                    "thread_id": thread_id,
                }

            return {
                "status": "needs_feedback",
                "post": interrupt_data.get("post"),
                "iteration": interrupt_data.get("iteration"),
                "thread_id": thread_id,
            }

        if values.get("post_status"):
            return {
                "status": result.get("post_status"),
                "post_id": result.get("post_id"),
                "reason": result.get("reason"),
                "post": result.get("post"),
                "thread_id": thread_id
            }

        return {
            "status": "ERROR",
            "reason": "Rate limit exceeded or unknown error. Try again later.",
            "post": values.get("generated_post", ""),
            "thread_id": thread_id
        }

    except Exception as e:
        return {
            "status": "ERROR",
            "reason": str(e),
        }