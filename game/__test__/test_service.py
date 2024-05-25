import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from redis import Redis
from fastapi import HTTPException
from game.model import GameModel, CreateGameModel, UpdateGameModel
from game.schema import GameSchema
from game.service import create, update
import os
import json

os.environ["GAME_EXPIRE_TIME"] = "0"

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

@patch('game.model.GameModel.model_validate', return_value=GameModel(**{**mock_game_model_dict, 'status': "INIT"}))
@patch('game.model.UpdateGameModel.model_validate', return_value=UpdateGameModel(**{"turn": mock_game_model_dict['player1'], "move": [0, 1]}))
def test_update_game(mock_db, mock_redis):
    mock_db.query.return_value.filter.return_value.first.return_value = GameSchema(**{**mock_game_schema_dict})

    mock_redis.hget.return_value.decode.return_value.replace.return_value = json.dumps(mock_game_model_dict)
    mock_redis.hset.return_value = None
    mock_redis.expire.return_value = None

    result = update(UpdateGameModel(turn="Alice", move=[0, 1]), "123", mock_db, mock_redis)

    assert result['player1'] == mock_game_schema_dict['player1']
    assert result['player2'] == mock_game_schema_dict['player2']
    assert result['player1_symbol'] == mock_game_schema_dict['player1_symbol']
    assert result['player2_symbol'] == mock_game_schema_dict['player2_symbol']
    assert result['status'] == "IN_PROGRESS"
    assert result['turn'] == mock_game_model_dict['player2']
    assert result['move'] == [0, 1]

@patch('game.model.GameModel.model_validate', return_value=GameModel(**{**mock_game_model_dict, "board":[['X', '', 'X'], ['', '', ''], ['', '', '']]}))
@patch('game.model.UpdateGameModel.model_validate', return_value=UpdateGameModel(**{"turn": mock_game_model_dict['player1'], "move": [0, 1]}))
def test_update_game_win_game(mock_db, mock_redis):
    mock_db.query.return_value.filter.return_value.first.return_value = GameSchema(**mock_game_schema_dict)
    
    mock_redis.hget.return_value.decode.return_value.replace.return_value = json.dumps(mock_game_model_dict)
    mock_redis.hexists.return_value = True

    
    result = update(UpdateGameModel(turn=mock_game_model_dict['player1'], move=[0, 1]), "123", mock_db, mock_redis)

    assert result["is_over"] == True
    assert result["winner"] == mock_game_model_dict['player1']
    assert result["is_draw"] == False
    assert result["status"] == "FINISH"
    assert mock_db.commit.call_count == 1

@patch('game.model.GameModel.model_validate', return_value=GameModel(**{**mock_game_model_dict, "board":[['X', '', 'O'], ['O', 'O', 'X'], ['X', 'X', 'O']]}))
@patch('game.model.UpdateGameModel.model_validate', return_value=UpdateGameModel(**{"turn": mock_game_model_dict['player1'], "move": [0, 1]}))
def test_update_game_draw_game(mock_db, mock_redis):
    mock_db.query.return_value.filter.return_value.first.return_value = GameSchema(**mock_game_schema_dict)
    
    mock_redis.hget.return_value.decode.return_value.replace.return_value = json.dumps(mock_game_model_dict)
    mock_redis.hexists.return_value = True

    
    result = update(UpdateGameModel(turn=mock_game_model_dict['player1'], move=[0, 1]), "123", mock_db, mock_redis)

    assert result["is_over"] == True
    assert result["winner"] == None
    assert result["is_draw"] == True
    assert result["status"] == "FINISH"
    assert mock_db.commit.call_count == 1

@patch('game.model.GameModel.model_validate', return_value=GameModel(**{**mock_game_model_dict, 'status': "INIT"}))
@patch('game.model.UpdateGameModel.model_validate', return_value=UpdateGameModel(**{"turn": mock_game_model_dict['player1'], "move": [0, 1]}))
def test_update_game_exeptions_1(mock_db, mock_redis):
    mock_db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as excinfo:
        update(UpdateGameModel(turn="Alice", move=[0, 1]), "123", mock_db, mock_redis)

    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Game not found"

    mock_db.query.return_value.filter.return_value.first.return_value = GameSchema(**mock_game_schema_dict)
    mock_redis.hexists.return_value = False

    with pytest.raises(HTTPException) as excinfo:
        update(UpdateGameModel(turn="Alice", move=[0, 1]), "123", mock_db, mock_redis)

    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Game has expired"

@patch('game.model.GameModel.model_validate', return_value=None)
@patch('game.model.UpdateGameModel.model_validate', return_value=UpdateGameModel(**{"turn": mock_game_model_dict['player1'], "move": [0, 1]}))
def test_update_game_exeptions_2(mock_db, mock_redis):
    mock_db.query.return_value.filter.return_value.first.return_value = GameSchema(**mock_game_schema_dict)
    
    mock_redis.hget.return_value.decode.return_value.replace.return_value = json.dumps(mock_game_model_dict)
    mock_redis.hexists.return_value = True

    with pytest.raises(HTTPException) as excinfo:
        update(UpdateGameModel(turn="Alice", move=[0, 1]), "123", mock_db, mock_redis)

    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Game not found"


@patch('game.model.GameModel.model_validate', return_value=GameModel(**{**mock_game_model_dict, 'status': "INIT"}))
@patch('game.model.UpdateGameModel.model_validate', return_value=UpdateGameModel(**{"turn": mock_game_model_dict['player2'], "move": [0, 1]}))
def test_update_game_exeptions_3(mock_db, mock_redis):
    mock_db.query.return_value.filter.return_value.first.return_value = GameSchema(**mock_game_schema_dict)
    
    mock_redis.hget.return_value.decode.return_value.replace.return_value = json.dumps(mock_game_model_dict)
    mock_redis.hexists.return_value = True

    with pytest.raises(HTTPException) as excinfo:
        update(UpdateGameModel(turn="Bob", move=[0, 1]), "123", mock_db, mock_redis)

    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "It's not your turn"

@patch('game.model.GameModel.model_validate', return_value=GameModel(**{**mock_game_model_dict, 'is_over': True}))
@patch('game.model.UpdateGameModel.model_validate', return_value=UpdateGameModel(**{"turn": mock_game_model_dict['player1'], "move": [0, 1]}))
def test_update_game_exeptions_4(mock_db, mock_redis):
    mock_db.query.return_value.filter.return_value.first.return_value = GameSchema(**mock_game_schema_dict)
    
    mock_redis.hget.return_value.decode.return_value.replace.return_value = json.dumps(mock_game_model_dict)
    mock_redis.hexists.return_value = True

    with pytest.raises(HTTPException) as excinfo:
        update(UpdateGameModel(turn=mock_game_model_dict['player1'], move=[0, 1]), "123", mock_db, mock_redis)

    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "Game is over"

@patch('game.model.GameModel.model_validate', return_value=GameModel(**{**mock_game_model_dict}))
@patch('game.model.UpdateGameModel.model_validate', return_value=UpdateGameModel(**{"turn": mock_game_model_dict['player1'], "move": [0, 1, 2]}))
def test_update_game_exeptions_5(mock_db, mock_redis):
    mock_db.query.return_value.filter.return_value.first.return_value = GameSchema(**mock_game_schema_dict)
    
    mock_redis.hget.return_value.decode.return_value.replace.return_value = json.dumps(mock_game_model_dict)
    mock_redis.hexists.return_value = True

    with pytest.raises(HTTPException) as excinfo:
        update(UpdateGameModel(turn=mock_game_model_dict['player1'], move=[0, 1, 2]), "123", mock_db, mock_redis)

    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "Invalid move"

@patch('game.model.GameModel.model_validate', return_value=GameModel(**{**mock_game_model_dict}))
@patch('game.model.UpdateGameModel.model_validate', return_value=UpdateGameModel(**{"turn": "Should return invalid turn", "move": [0, 1]}))
def test_update_game_exeptions_6(mock_db, mock_redis):
    mock_db.query.return_value.filter.return_value.first.return_value = GameSchema(**mock_game_schema_dict)
    
    mock_redis.hget.return_value.decode.return_value.replace.return_value = json.dumps(mock_game_model_dict)
    mock_redis.hexists.return_value = True

    with pytest.raises(HTTPException) as excinfo:
        update(UpdateGameModel(turn="Should return invalid turn", move=[0, 1]), "123", mock_db, mock_redis)

    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "It's not your turn"

@patch('game.model.GameModel.model_validate', return_value=GameModel(**{**mock_game_model_dict, "board":[['', 'X', ''], ['', '', ''], ['', '', '']]}))
@patch('game.model.UpdateGameModel.model_validate', return_value=UpdateGameModel(**{"turn": mock_game_model_dict['player1'], "move": [0, 1]}))
def test_update_game_exeptions_7(mock_db, mock_redis):
    mock_db.query.return_value.filter.return_value.first.return_value = GameSchema(**mock_game_schema_dict)
    
    mock_redis.hget.return_value.decode.return_value.replace.return_value = json.dumps(mock_game_model_dict)
    mock_redis.hexists.return_value = True

    with pytest.raises(HTTPException) as excinfo:
        update(UpdateGameModel(turn=mock_game_model_dict['player1'], move=[0, 1]), "123", mock_db, mock_redis)

    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "Invalid move"

@patch('game.model.GameModel.model_validate', return_value=GameModel(**{**mock_game_model_dict}))
@patch('game.model.UpdateGameModel.model_validate', return_value=UpdateGameModel(**{"turn": mock_game_model_dict['player1'], "move": [0, 5]}))
def test_update_game_exeptions_8(mock_db, mock_redis):
    mock_db.query.return_value.filter.return_value.first.return_value = GameSchema(**mock_game_schema_dict)
    
    mock_redis.hget.return_value.decode.return_value.replace.return_value = json.dumps(mock_game_model_dict)
    mock_redis.hexists.return_value = True

    with pytest.raises(HTTPException) as excinfo:
        update(UpdateGameModel(turn=mock_game_model_dict['player1'], move=[0, 5]), "123", mock_db, mock_redis)

    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "Invalid move"