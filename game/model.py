from pydantic import BaseModel
from typing import Optional, List

class GameModel(BaseModel):
    id: int
    board: Optional[tuple] = None
    winner: Optional[str] = None
    is_draw: bool
    is_over: bool
    player1: str
    player2: Optional[str] = None
    player2_symbol: Optional[str] = None
    player1_symbol: str
    move: Optional[List[int]] = None
    turn: Optional[str] = None
    status: str
    created_by: str
    updated_by: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True

class CreateGameModel(BaseModel):
    player: Optional[str] = None

class UpdateGameModel(BaseModel):
    turn: str
    move: List



