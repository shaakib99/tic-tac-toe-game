import redis
import os

class RedisDB:
    instance = None
    def __init__(self):
        self.redis  = redis.Redis(host = os.getenv('REDIS_URL', 'localhost'))
        # self.subscribe_to_expirations()

    @staticmethod
    def get_db():
        return RedisDB.get_instance().redis

    @staticmethod
    def get_instance():
        if RedisDB.instance is None:
            RedisDB.instance = RedisDB()
        return RedisDB.instance
    
    def subscribe_to_expirations(self):
        pubsub = self.redis.pubsub()

        # Subscribe to the keyevent@0__:expired channel
        pubsub.subscribe(**{'__keyevent@0__:expired': lambda x: print(x)})
        pubsub.run_in_thread(sleep_time=0.001)