from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func

from app.core.db import Base


class Entry(Base):
    __tablename__ = "entries"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    category = Column(String(50), nullable=True)

    estimated_min = Column(Integer, nullable=False)
    actual_min = Column(Integer, nullable=False)

    difficulty = Column(Integer, nullable=False)   # 1–5
    mood = Column(Integer, nullable=False)         # 1–5
    distractions = Column(Integer, nullable=False) # 0–5

    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)