from pydantic import BaseModel
from typing import Optional

class GameModel(BaseModel):
    board: list[list[str]]
    winner: Optional[str]
    is_draw: Optional[bool]
    is_over: Optional[bool]
    player1: Optional[str]
    player2: Optional[str]
    player2_symbol: Optional[str]
    player1_symbol: Optional[str]
    move: list[int, int]
    turn: Optional[str]
    status: Optional[str]

class CreateGameModel(BaseModel):
    player1: str
    player2: Optional[str]

class UpdateGameModel(BaseModel):
    turn: str
    move: list[int, int]



