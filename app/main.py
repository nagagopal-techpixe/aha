# app/main.py
from fastapi import FastAPI
from app.routes import router as review_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Movie Review API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For testing only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routes
app.include_router(review_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)