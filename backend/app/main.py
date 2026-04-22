from fastapi import FastAPI
from app.routes.simulate import router

app = FastAPI()
app.include_router(router)
