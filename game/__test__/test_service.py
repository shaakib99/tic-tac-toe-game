import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from redis import Redis
from fastapi import HTTPException
from game.model import GameModel, CreateGameModel
from game.schema import GameSchema
from game.service import create
import os

os.environ["GAME_EXPIRE_TIME"] = "180"

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
        "created_by": "Admin",
        "updated_by": "Alice",
        "created_at": "2024-05-20T12:00:00Z",
        "updated_at": "2024-05-20T12:00:00Z"
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


@patch('game.model.GameModel.model_validate', return_value=GameModel(**{**mock_game_schema_dict, 'player2': None}))
def test_create_game(mock_db, mock_redis, mock_create_game_data):
    
    result = create(mock_create_game_data, mock_db, mock_redis)
    assert result['player1'] == mock_game_schema_dict['player1']
    assert result['player2'] == None
    assert result['player1_symbol'] == mock_game_schema_dict['player1_symbol']
    assert result['player2_symbol'] == mock_game_schema_dict['player2_symbol']
    assert result['status'] == mock_game_schema_dict['status']
    assert result['turn'] == mock_game_schema_dict['player1']

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


@patch('game.model.GameModel.model_validate', return_value=GameModel(**{**mock_game_schema_dict, 'status': "INIT"}))
def test_join_game(mock_db, mock_redis, mock_create_game_data):
    mock_db.filter.return_value.limit.return_value.count.return_value = 1
    mock_db.query.filter.return_value.limit.return_value.first.return_value = GameModel(**mock_game_schema_dict)

    mock_redis.hset.return_value = True
    mock_redis.expire.return_value = True


    result = create(mock_create_game_data, mock_db, mock_redis)
    assert result['player1'] == mock_game_schema_dict['player1']
    assert result['player2'] == mock_game_schema_dict['player2']
    assert result['player1_symbol'] == mock_game_schema_dict['player1_symbol']
    assert result['player2_symbol'] == mock_game_schema_dict['player2_symbol']
    assert result['status'] == "INIT"
    assert result['turn'] == mock_game_schema_dict['player1']

    assert mock_db.add.call_count == 1
    mock_db.commit.assert_called_once()

@pytest.fixture
def test_exceptions(mock_db, mock_redis, mock_create_game_data):
    mock_db.filter.return_value.limit.return_value.count.return_value = 0

    with pytest.raises(HTTPException) as excinfo:
        create(mock_create_game_data, mock_db, mock_redis, game_id="123")

    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Game not found"

    mock_db.filter.return_value.limit.return_value.count.return_value = 1
    mock_db.filter.return_value.limit.return_value.first.return_value = GameSchema(**{**mock_game_schema_dict, "is_over": True})

    with pytest.raises(HTTPException) as excinfo:
        create(mock_create_game_data, mock_db, mock_redis, game_id="123")

    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "Game is over"

    mock_db.filter.return_value.limit.return_value.first.return_value = GameSchema(**{**mock_game_schema_dict})

    with pytest.raises(HTTPException) as excinfo:
        create(mock_create_game_data, mock_db, mock_redis, game_id="123")

    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "Game is full"

    mock_redis.hexists.return_value = False

    with pytest.raises(HTTPException) as excinfo:
        create(mock_create_game_data, mock_db, mock_redis, game_id="123")
    
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Game has expired"

