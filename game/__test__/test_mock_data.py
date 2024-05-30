from unittest.mock import MagicMock
import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session
from redis import Redis
from game.model import GameModel, CreateGameModel, UpdateGameModel
import os

mock_game_schema_dict = {
        "id": 1,
        "player1": "Alice",
        "player2": "Bob",
        "player1_symbol": "X",
        "player2_symbol": "O",
        "turn": "Alice",
        "status": "CREATE",
        "is_over": False,
        "is_draw": False,
        "created_by": "Alice",
        "updated_by": "Alice",
        "created_at": "2024-05-20T12:00:00Z",
        "updated_at": "2024-05-20T12:00:00Z"
}

mock_game_model_dict = {
    **mock_game_schema_dict,
    "board": [['', '', ''], ['', '', ''], ['', '', '']],
}



@pytest.fixture
def mock_db():
    db = MagicMock(spec=Session)
    return db

@pytest.fixture
def mock_redis():
    redis = MagicMock(spec=Redis)
    return redis

@pytest.fixture
def mock_create_game_data():
    return CreateGameModel(player="player1")

def set_environment_variables():
    os.environ["GAME_EXPIRE_TIME"] = "30"
    os.environ["DB_CONNECTION"] =  "mysql://root:root@localhost:3306/tic_tac_toe_test"
    os.environ["REDIS_URL"] = "localhost"
