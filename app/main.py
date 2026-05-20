from fastapi import FastAPI
from app.database import init_db
from app.routers.api_router import router as api_router
from app.routers.web_router import router as web_router

app = FastAPI(title="bookmark-curator-agent", version="0.1.0")


@app.on_event("startup")
def startup() -> None:
    init_db()


app.include_router(web_router)
app.include_router(api_router)
