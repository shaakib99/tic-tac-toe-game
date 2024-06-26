import redis
from dotenv import load_dotenv
import os

load_dotenv()

class RedisDB:
    instance = None
    def __init__(self):
        self.redis  = redis.Redis(host = os.getenv('REDIS_URL', 'localhost'))

    @staticmethod
    def get_db():
        return RedisDB.get_instance().redis

    @staticmethod
    def get_instance():
        if RedisDB.instance is None:
            RedisDB.instance = RedisDB()
        return RedisDB.instance