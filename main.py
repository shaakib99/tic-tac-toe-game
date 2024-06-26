from fastapi import FastAPI, WebSocket
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from dotenv import load_dotenv
from game.router import router as game_router
from database import DB
from redis_database import RedisDB
import logging
import uvicorn
import os

load_dotenv()

logger = logging.getLogger("uvicorn")

def lifespan(app: FastAPI):
    # before app start

    # check database connection & create tables if necessary
    db = DB.get_instance()
    db.engine.connect()
    db.Base.metadata.create_all(bind=db.engine)
    logger.info("Database connection established")

    # check redis connection
    redis_db = RedisDB.get_db()
    redis_db.ping()
    logger.info("Redis connection established")
    yield

    # after app stop

    # close database connection
    DB.close_db_connection()
    redis_db.close()


app = FastAPI(lifespan=lifespan)

# Route dependencies
routers = [game_router]

for router in routers:
    app.include_router(router)

# Default middlewares
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"],allow_headers=["*"])
app.add_middleware(GZipMiddleware, minimum_size=1000)

# start app
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv('PORT', 5000)), reload=True)


