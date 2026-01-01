from fastapi import APIRouter, Header, HTTPException
from api.schemas import GenerateRequest, NeedsFeedbackResponse, FinalPostResponse, FinalSearchResponse, ErrorResponse, SearchResponse
from graph.nodes import State
from graph.workflow import build_graph
from typing import Union, Any, Optional

workflow = build_graph()

def raise_error(*, status_code: int, message: str, debug: Any = None):
    raise HTTPException(
        status_code=status_code,
        detail={
            "status": "error",
            "message": message,
            "debug": debug,
        },
    )

response_model = Union[
    NeedsFeedbackResponse,
    FinalPostResponse,
    FinalSearchResponse,
    ErrorResponse,
    SearchResponse
]

router = APIRouter(prefix="/generate", tags=["Generate"])

@router.post("/", response_model=response_model)
async def generate(
    req: GenerateRequest,
    
    x_twitter_bearer: Optional[str] = Header(None),
    x_twitter_api_key: Optional[str] = Header(None),
    x_twitter_api_secret: Optional[str] = Header(None),
    x_twitter_access_token: Optional[str] = Header(None),
    x_twitter_access_secret: Optional[str] = Header(None),
    x_groq_api_key: Optional[str] = Header(None)
):
    """
    Start a new workflow using user-provided API keys
    """
    
    
    config = {
        "configurable": {
            "thread_id": "tweet-1",
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

    initial_state: State = {
        "chosen_tool": "",
        "input": req.input,                
        "human_feedback" : [],
        "iteration": 1,
        "max_iteration": 5,
        "tweet_topic":"",
        "generated_post":[],
        "post_result":"",
        "search_result":"",
        "search_tweet":"",
        "error":"",
        "error_type":"",
        "final_tweet":"",
        "trace":"",
        "post":"",
        "post_id":"",
        "post_status":"",
        "reason":""
    }

    try:
        
        result = await workflow.ainvoke(initial_state, config)

        if "__interrupt__" in result:
            interrupt_data = result["__interrupt__"][0].value
            return {
                "status": "needs_feedback",
                "post": interrupt_data["post"],
                "iteration": interrupt_data["iteration"],
                "thread_id": "tweet-1"
            }

        
        state = workflow.get_state(config)
        values = state.values 
        
        print(f"Values : {values}")
        
        if values.get("error"):
        
                error_type = values.get("error_type", "UNKNOWN")

                if error_type == "RATE_LIMIT":
                    raise_error(
                        status_code=429,
                        message="API-Rate limit Exceeded. Try Again after Sometime.....",
                            
                        
                        debug=values.get("trace"),
                    )

                elif error_type == "MCP_ERROR":
                    raise_error(
                        status_code=404,
                        message= "User not found or protected. PLEASE ENTER CORRECT USER NAME.",
                            
                           
                        
                        debug=values.get("trace"),
                    )

                elif error_type == "TOOL_EXECUTION_ERROR":
                    raise_error(
                        status_code=502,
                        message="External service failed.",
                        debug=values.get("trace"),
                    )

                else:
                    raise_error(
                    status_code=500,
                    message="Something went wrong.",
                    debug=values,
                )


        
        if values.get("search_result"):
            return {
                "status": "done",
                "type": "search",
                "output": values["search_result"],
            }
        
        if values.get("search_tweet"):
            return {
                "status": "SKIPPED",
                "type": "Error 429",
                "reason": "X API rate limit hit (search). Skipping search.",
                "Tweet" : "[]"
            }
        
        
        

    except HTTPException:
        raise

    except Exception as e:
        
        raise_error(
            status_code=500,
            message="Internal server error.",
            debug=str(e),
        )