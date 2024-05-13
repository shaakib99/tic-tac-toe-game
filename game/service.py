from fastapi import HTTPException
from typing import Optional
from database import DB
from redis_database import RedisDB
from .model import CreateGameModel, GameModel, UpdateGameModel
from .schema import GameSchema
from datetime import datetime
import os

db = DB.get_db()
redis_db = RedisDB.get_db()

def create(data: CreateGameModel, game_id: Optional[str] = None) -> dict:
    game = None
    if game_id is not None:
        game_exist = db.query(GameSchema).filter(id == game_id).limit(1)

        if game_exist.count() == 0:
            raise HTTPException(status_code=404, detail="Game not found")
        if game_exist.first().is_over:
            raise HTTPException(status_code=400, detail="Game is over")
        if game_exist.first().player1 is not None and game_exist.first().player2 is not None:
            raise HTTPException(status_code=400, detail="Game is full")
        
        game = game_exist.first()
    
    if game is None:
        game = GameSchema(**data.model_dump())

    game.player1_symbol = 'X'
    game.player2_symbol = 'O'
    game.turn = game.player1

    if game.player1 is not None and game.player2 is not None:
        game.status = 'INIT'
    else:
        game.status = 'CREATE'
    
    game.updated_at = datetime.now().__str__()
    game.updated_by = data.player2
    game.created_by = game.player1 or data.player1
    db.add(game)
    db.commit()
    gameModel = GameModel.model_validate(game, from_attributes=True, strict=False)
    gameModel.board = ['', '', ''], ['', '', ''], ['', '', '']

    # add to redis
    redis_db.set(f"GAME_{game_id}", gameModel.model_dump(), os.getenv('GAME_EXPIRE', 30)) # game expires in 30 seconds

    return gameModel.model_dump()

def update(data: UpdateGameModel, game_id: str):
    game = GameModel.model_validate_json(redis_db.get(f"GAME_{game_id}"))
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    if game.turn == data.turn:
        raise HTTPException(status_code=400, detail="It's not your turn")
    if game.is_over:
        raise HTTPException(status_code=400, detail="Game is over")
    if len(data.move) != 2: 
        raise HTTPException(status_code=400, detail="Invalid move")
    if 0 < data.move[0] <  2 or 0 < data.move[1] <  2:
        raise HTTPException(status_code=400, detail="Invalid move") 


    if game is None:
        game.status = "EXPIRED"
        db.add(game)
        db.commit()
        raise HTTPException(status_code=404, detail="Game has been expired")
    
    game.id = game.id

    board = game.board
    
    if board[data.move[0]][data.move[1]] != '':
        raise HTTPException(status_code=400, detail="Invalid move")

    symbol = ''
    if data.turn == game.player1:
        symbol = game.player1_symbol
    else:
        symbol = game.player2_symbol

    board[data.move[0]][data.move[1]] = symbol

    game.move = data.move

    isOver = False
    if board[data.move[0]][0] == symbol and board[data.move[0]][1] == symbol and board[data.move[0]][2] == symbol:
        isOver = True
    if board[0][data.move[1]] == symbol and board[1][data.move[1]] == symbol and board[2][data.move[1]] == symbol:
        isOver = True
    if board[0][0] == symbol and board[1][1] == symbol and board[2][2] == symbol:
        isOver = True
    if board[0][2] == symbol and board[1][1] == symbol and board[2][0] == symbol:
        isOver = True

    if isOver:
        game.is_over = True
        game.winner = data.turn
        game.updated_at = datetime.now().__str__()
        game.updated_by = data.turn
        game.board = board
        game.status = 'FINISH'
        game.is_draw = False
    elif board[0][0] != '' and board[0][1] != '' and board[0][2] != '' and board[1][0] != '' and board[1][1] != '' and board[1][2] != '' and board[2][0] != '' and board[2][1] != '' and board[2][2] != '':
        game.is_draw = True
        game.isOver = True
        game.status = 'FINISH'
        game.winner = None
    else:
        game.is_over = False
        game.is_draw = False
        game.turn = game.player2 if data.turn == game.player1 else game.player1
    
    game.updated_at = datetime.now().__str__()
    game.updated_by = data.turn
    game.board = board

    if game.is_over:
        db.add(GameSchema(**game.model_dump()))
        db.commit()

    redis_db.set(f"GAME_{game_id}", game.model_dump(), os.getenv('GAME_EXPIRE', 30)) # game expires in 30 seconds
    return game.model_dump()