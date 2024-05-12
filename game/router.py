from fastapi import APIRouter, status
from typing import Optional

router = APIRouter()
router.prefix = '/games/'

@router.post('', status_code=status.HTTP_201_CREATED, summary="Create new game")
async def create(data: dict) -> dict:
    return data

@router.post('{game_id}', status_code=status.HTTP_201_CREATED, summary="New player can join the game using game_id")
async def join(data: dict, game_id: Optional[str]) -> dict:
    print(data, game_id)
    return data