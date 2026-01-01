from pydantic import BaseModel

class GenerateRequest(BaseModel):
    input: str

class ResumeRequest(BaseModel):
    feedback: str
    


class ResumeResponse(BaseModel):
    output: str

from typing import Literal
from pydantic import BaseModel

class NeedsFeedbackResponse(BaseModel):
    status: Literal["needs_feedback"]
    post: str
    iteration: int
    thread_id: str

class FinalPostResponse(BaseModel):
    status: Literal["done"]
    type: Literal["post"]
    output: str

class FinalSearchResponse(BaseModel):
    status: Literal["done"]
    type: Literal["search"]
    output: dict


class ErrorResponse(BaseModel):
    status: Literal["error"]
    message: str
    details: dict | None = None

class SearchResponse(BaseModel):
    status: str
    type: str
    reason: str
    Tweet: str
        
    