from fastapi import APIRouter, status, Depends, WebSocketDisconnect, WebSocket, HTTPException
from typing import Optional
from game.model import CreateGameModel, GameModel
import game.service as gameService
from redis_database import RedisDB
from database import DB
from websocket_connection_manager import WSConnectionManager

router = APIRouter(prefix='/games', tags=['Game'])

@router.post('', status_code=status.HTTP_201_CREATED, response_model= GameModel, summary="Create new game")
async def create(data: CreateGameModel, db = Depends(DB.get_db), redis_db = Depends(RedisDB.get_db)):
    return gameService.create(data, db, redis_db)

@router.post('/{game_id}', status_code=status.HTTP_201_CREATED, response_model= GameModel, summary="New player can join the game using game_id")
async def join(data: CreateGameModel, game_id: Optional[str], db = Depends(DB.get_db), redis_db = Depends(RedisDB.get_db)) -> dict:
    return gameService.create(data, db, redis_db, game_id)


@router.websocket("/ws/{game_id}", name="Play Game")
async def update_game(websocket: WebSocket, game_id: str, db = Depends(DB.get_db), redis_db = Depends(RedisDB.get_db)):
    connectionManger = WSConnectionManager.get_instance()
    await connectionManger.connect(websocket, game_id)
    await connectionManger.broadcast({"message": "New Player joined game..."}, game_id, exclude = [websocket]);
    while True:
        try:
            data = await websocket.receive_json()
            response = gameService.update(data, game_id, db, redis_db)
            await connectionManger.broadcast(response, game_id, exclude = [])
        except WebSocketDisconnect:
            await connectionManger.disconnect(websocket, game_id)
            await connectionManger.broadcast(f"Player disconnected from game {game_id}", game_id, exclude = [websocket])
        except HTTPException as httpex:
            message = httpex.detail
            await connectionManger.send_personal_message({"error": message}, websocket)
            break
        except Exception as e:
            if websocket.client_state.name not in ( "DISCONNECTED", "CONNECTING"): 
                 await connectionManger.send_personal_message({"error": e.__str__()}, websocket)
            else: break