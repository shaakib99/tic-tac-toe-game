from fastapi import HTTPException
from sqlalchemy.orm import Session
from redis import Redis
from typing import Optional
from .model import CreateGameModel, GameModel, UpdateGameModel
from .schema import GameSchema
from datetime import datetime
import os
import json

def create(data: CreateGameModel, db:Session, redis_db:Redis, game_id: Optional[str] = None) -> dict:
    game = None
    if game_id is not None:
        game_exist = db.query(GameSchema).filter(GameSchema.id == game_id).limit(1)

        if game_exist.count() == 0:
            raise HTTPException(status_code=404, detail="Game not found")
        if game_exist.first().is_over:
            raise HTTPException(status_code=400, detail="Game is over")
        if game_exist.first().player1 is not None and game_exist.first().player2 is not None:
            raise HTTPException(status_code=400, detail="Game is full")
        if redis_db.hexists(f"GAME_{game_id}", "data") == False:
            raise HTTPException(status_code=404, detail="Game has expired")    
        
        game = game_exist.first()
        game.player2 = data.player

    if game is None:
        game = GameSchema(**data.model_dump(exclude=['player']))
        game.player1 = data.player

    game.player1_symbol = 'X'
    game.player2_symbol = 'O'
    game.turn = game.player1

    if game.player1 is not None and game.player2 is not None:
        game.status = 'INIT'
    else:
        game.status = 'CREATE'
    
    game.updated_at = datetime.now().__str__()
    game.updated_by = data.player
    game.created_by = game.player1 or data.player
    db.add(game)
    db.commit()
    gameModel = GameModel.model_validate(game, from_attributes=True, strict=False)
    gameModel.board = ['', '', ''], ['', '', ''], ['', '', '']

    # add to redis
    redis_db.hset(f"GAME_{game.id}", "data", json.dumps(gameModel.model_dump())) # game expires in 30 seconds

    return gameModel.model_dump()

def update(update_data: UpdateGameModel, game_id: str, db:Session, redis_db:Redis):
    data = UpdateGameModel.model_validate(update_data, from_attributes=True, strict=False)
    if db.query(GameSchema).filter(GameSchema.id == game_id).first() == None:
        raise HTTPException(status_code=404, detail="Game not found")
    if redis_db.hexists(f"GAME_{game_id}", "data") == False:
        raise HTTPException(status_code=404, detail="Game has expired")
    
    game_data = redis_db.hget(f"GAME_{game_id}", "data").decode('utf-8').replace("'", '"')
    game = GameModel.model_validate(json.loads(game_data), from_attributes=True, strict=False)

    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    if game.turn != data.turn:
        raise HTTPException(status_code=400, detail="It's not your turn")
    if game.is_over:
        raise HTTPException(status_code=400, detail="Game is over")
    if len(data.move) != 2: 
        raise HTTPException(status_code=400, detail="Invalid move")
    if 0 > data.move[0]  or data.move[0] >  2 or 0 > data.move[1] or data.move[1]    >  2:
        raise HTTPException(status_code=400, detail="Invalid move") 
    if game.player1 != data.turn and game.player2 != data.turn:
        raise HTTPException(status_code=400, detail="It's not your turn")
    
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
        game.status = 'IN_PROGRESS'
        game.turn = game.player2 if data.turn == game.player1 else game.player1
    
    game.updated_at = datetime.now().__str__()
    game.updated_by = data.turn
    game.board = board

    if game.is_over:
        GameSchema(**game.model_dump(exclude=['board', 'move']))
        db.commit()

    redis_db.hset(f"GAME_{game_id}","data", json.dumps(game.model_dump()))
    redis_db.expire(f"GAME_{game_id}", 30)
    return game.model_dump()