import uvicorn

from core.settings import settings
from service.server import create_server


if __name__ == "__main__":
    uvicorn.run(create_server(), host=settings.server_host, port=settings.server_port)
