
from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List, TYPE_CHECKING
from app.core.db import Base
if TYPE_CHECKING:
    from .post import PostORM



class AuthorORM(Base):
    __tablename__ = "authors"
    id : Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name : Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, unique=True, index=True)
    
    posts: Mapped[List["PostORM"]] = relationship(back_populates="author")