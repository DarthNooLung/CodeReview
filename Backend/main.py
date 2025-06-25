from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import format, review, gpt_format, sast

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(format.router)
app.include_router(review.router)
app.include_router(gpt_format.router)
app.include_router(sast.router)

# 아래는 uvicorn 실행용 예시
# python -m uvicorn main:app --reload --port 8513