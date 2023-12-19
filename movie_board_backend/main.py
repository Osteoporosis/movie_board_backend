from __future__ import annotations

import fastapi
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

from .configs import DOMAIN_NAME
from .routers import movies, users

origins: list[str] = [
    f"https://{DOMAIN_NAME}",
    f"http://{DOMAIN_NAME}",
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:8080",
]


app = fastapi.FastAPI()

app.add_middleware(
    middleware_class=CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(movies.router)
app.include_router(users.router)


# for debugging
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)  # type: ignore[]  # noqa: S104
