from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List,TYPE_CHECKING
from app.core.db import Base
from app.models.post import post_tags
if TYPE_CHECKING:
    from .post import PostORM
    
class TagORM(Base):
    __tablename__ = "tags"
    id : Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name : Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    
    posts: Mapped[List["PostORM"]] = relationship(
        secondary=post_tags,
        back_populates="tags",
        lazy="selectin",
        passive_deletes=True
    )
    
    