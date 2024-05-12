from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from dotenv import load_dotenv
from game.router import router as game_router
import uvicorn
import os

load_dotenv()


app = FastAPI()

# Route dependencies
routers = [game_router]

# Middleware dependecies
middlewares = []


for router in routers:
    app.include_router(router)

# Default middlewares
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
app.add_middleware(GZipMiddleware, minimum_size=1000)

# add custom middleware
for mw in middlewares:
    app.add_middleware(mw)

# start app
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv('PORT', 5000)), reload=True)


