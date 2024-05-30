from game.service import create, update
from game.__test__.test_mock_data import mock_game_model_dict, mock_game_schema_dict, mock_db, mock_redis
from game.model import CreateGameModel, UpdateGameModel
from game.schema import GameSchema
from database import DB
from redis_database import RedisDB
import pytest
import os

def test_set_environment_variables():
    assert os.getenv("DB_CONNECTION") ==  "mysql://root:root@localhost:3306/tic_tac_toe_test"
    assert os.getenv("REDIS_URL") == "localhost"
    # assert os.getenv("GAME_EXPIRE_TIME") == "30"


@pytest.fixture()
def mock_db():
    db = DB.get_instance()
    db.get_base().metadata.create_all(bind=db.engine)
    try:
        yield db.get_db()
    finally:
        db.get_db().rollback()
        db.close_db_connection()

@pytest.fixture()
def mock_redis():
    redis = RedisDB.get_instance()
    try:
        yield redis.get_db()
    finally:
        redis.get_db().close()

def test_create(mock_db, mock_redis):
    game = create(CreateGameModel(player=mock_game_model_dict["player1"]), mock_db, mock_redis, None)
    assert game["player1"] == mock_game_model_dict["player1"]
    assert game["player2"] == None
    assert game["player1_symbol"] == mock_game_model_dict["player1_symbol"]
    assert game["turn"] == mock_game_model_dict["turn"]
    assert game["status"] == mock_game_model_dict["status"]
    assert game["is_over"]== mock_game_model_dict["is_over"]
    assert game["is_draw"] == mock_game_model_dict["is_draw"]
    assert game["created_by"] == mock_game_model_dict["created_by"]
    assert game["updated_by"] == mock_game_model_dict["updated_by"]

    game_exist = mock_db.query(GameSchema).filter(GameSchema.id == game["id"]).limit(1)
    assert game_exist.count() == 1
    # exist =  mock_redis.hexists(f"GAME_{game["id"]}", "data")
    # assert exist == True

def test_join(mock_db, mock_redis):
    game = create(CreateGameModel(player=mock_game_model_dict["player1"]), mock_db, mock_redis, None)
    game = create(CreateGameModel(player=mock_game_model_dict["player2"]), mock_db, mock_redis, game_id=game["id"])
    assert game["player1"] == mock_game_model_dict["player1"]
    assert game["player2"] == mock_game_model_dict["player2"]
    assert game["player1_symbol"] == mock_game_model_dict["player1_symbol"]
    assert game["player2_symbol"] == mock_game_model_dict["player2_symbol"]
    assert game["status"] == "INIT"
    assert game["turn"] == mock_game_model_dict["player1"]
    assert game["is_over"]== mock_game_model_dict["is_over"]
    assert game["is_draw"] == mock_game_model_dict["is_draw"]
    assert game["created_by"] == mock_game_model_dict["created_by"]
    assert game["updated_by"] == mock_game_model_dict["player2"]

    game_exist = mock_db.query(GameSchema).filter(GameSchema.id == game["id"]).limit(1)
    assert game_exist.count() == 1

def test_update(mock_db, mock_redis):
    game = create(CreateGameModel(player=mock_game_model_dict["player1"]), mock_db, mock_redis, None)
    game = create(CreateGameModel(player=mock_game_model_dict["player2"]), mock_db, mock_redis, game["id"])
    update_game = update(UpdateGameModel(turn=mock_game_model_dict["player1"], move=[0,0]), game["id"], mock_db, mock_redis)
    assert update_game["board"][0][0] == mock_game_model_dict['player1_symbol']
    assert update_game["turn"] == mock_game_model_dict["player2"]
    assert update_game["status"] == "IN_PROGRESS"
    assert update_game["is_over"] == mock_game_model_dict["is_over"]
    assert update_game["is_draw"] == mock_game_model_dict["is_draw"]
    assert update_game["updated_by"] == mock_game_model_dict["player1"]
    assert update_game["created_by"] == mock_game_model_dict["player1"]