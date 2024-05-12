from sqlalchemy import Column, Integer, String, Boolean, ARRAY
from datetime import datetime
from database import DB

Base = DB.get_base()

class GameSchema(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    player1 = Column(String(50), nullable=True)
    player2 = Column(String(50), nullable=True)
    player1_symbol = Column(String(50), nullable=True)
    player2_symbol = Column(String(50), nullable=True)
    winner =  Column(String(50), nullable=True)
    is_draw = Column(Boolean(), nullable=True, default=False)
    is_over = Column(Boolean(), nullable=True, default=False)
    status = Column(String(50), nullable=False)
    turn = Column(String(50), nullable=True)
    created_by = Column(String(50), nullable=False)
    updated_by = Column(String(50), nullable=True)
    created_at = Column(String(50), nullable=False, default=datetime.now().__str__())
    updated_at = Column(String(50), nullable=True)

