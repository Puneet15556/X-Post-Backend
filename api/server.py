import os
import uvicorn
from fastapi import FastAPI
from api.router.generate import router as generate_router
from api.router.resume1 import router as resume_router

from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="X Post Generator")



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(generate_router)
app.include_router(resume_router)


@app.get("/")
async def health():
    return {"status": "ok"}
