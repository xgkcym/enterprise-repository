
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from api.upload import router
import uvicorn
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许的前端地址
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有 HTTP 方法
    allow_headers=["*"],  # 允许所有 Headers
)


app.include_router(router)
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=1016)