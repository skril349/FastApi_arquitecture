
# Consultas a bases de datos relacionados con tags

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.tag import TagORM


class TagRepository:
    def __init__(self, db:Session):
        self.db = db
        
    def create_tag(self, tag_name:str):
        normalize = tag_name.strip().lower()
        tag_obj = self.db.execute(
            select(TagORM).where(func.lower(TagORM.name) == normalize)
        ).scalar_one_or_none()
        
        if tag_obj:
            return tag_obj
        
        tag_obj = TagORM(name=tag_name)
        self.db.add(tag_obj)
        self.db.flush()
        return tag_obj