from fastapi import APIRouter, status
from typing import Optional
from game.model import CreateGameModel, GameModel, UpdateGameModel
import game.service as gameService

router = APIRouter()
router.prefix = '/games/'

@router.post('', status_code=status.HTTP_201_CREATED, response_model= GameModel, summary="Create new game")
async def create(data: CreateGameModel):
    return gameService.create(data)

@router.post('{game_id}', status_code=status.HTTP_201_CREATED, response_model= GameModel, summary="New player can join the game using game_id")
async def join(data: CreateGameModel, game_id: Optional[str]) -> dict:
    return gameService.create(data, game_id=game_id)

@router.patch('/{game_id}', status_code=status.HTTP_200_OK, response_model=GameModel, summary="Update game")
async def update(data: UpdateGameModel, game_id: Optional[str]):
    return {}