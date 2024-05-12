from fastapi import HTTPException
from typing import Optional
from database import DB
from .model import CreateGameModel, GameModel
from .schema import GameSchema
from datetime import datetime

db = DB.get_db()
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
    return gameModel.model_dump()