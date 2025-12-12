from sqlalchemy.orm import Session,selectinload, joinedload
from typing import List, Optional, Tuple
from app.models import PostORM, AuthorORM, TagORM
from app.core import db
from sqlalchemy import func, select

class PostRepository:
    def __init__(self, db:Session):
        self.db = db
        
    def get(self, post_id:int) -> Optional[PostORM]:
        post_find = select(PostORM).where(PostORM.id == post_id)
        return self.db.execute(post_find).scalar_one_or_none()
    
    def search(
        self,
        query:Optional[str] = None,
        order_by:Optional[str] = None,
        direction:Optional[str] = None,
        page:Optional[int] = None,
        per_page:Optional[int] = None) -> Tuple[int,List[PostORM]]:
        
        results = select(PostORM)        
        if query:
            # list comprehension to filter posts by title
            results =  results.where(PostORM.title.ilike(f"%{query}%"))
        
        total = self.db.scalar(select(func.count()).select_from(results.subquery()))
        
        if total == 0:
            return 0, []
        
        if order_by == "id":
            order_column = PostORM.id
        else:
            order_column = func.lower(PostORM.title)
        
        results = results.order_by(order_column.asc() if direction == "asc" else order_column.desc())
        items = self.db.execute(results.offset((page - 1) * per_page).limit(per_page)).scalars().all()
        
        return total, items
    
    def by_tags(self, tags:List[str]) -> List[PostORM]:
        normalized_tags_names = [tag.strip().lower() for tag in tags if tag.strip()]
        
        if not normalized_tags_names:
            return []
        
        post_list = select(PostORM).options(
            selectinload(PostORM.tags),
            joinedload(PostORM.author)).where(PostORM.tags.any(
                func.lower(TagORM.name).in_(normalized_tags_names)
            )).order_by(PostORM.id.asc())
            
        return self.db.execute(post_list).scalars().all()
        
    
    def ensure_author(self, name:str, email:Optional[str] = None) -> AuthorORM:
        
        author_obj = self.db.execute(
            select(AuthorORM).where(AuthorORM.email == email)
        ).scalar_one_or_none()
        
        if author_obj:
            return author_obj
        
        author_obj = AuthorORM(name=name, email=email)
        self.db.add(author_obj)
        self.db.flush()
        return author_obj
    
    def ensure_tag(self, tag_name:str) -> TagORM:
        tag_obj = self.db.execute(
            select(TagORM).where(func.lower(TagORM.name) == tag_name.lower())
        ).scalar_one_or_none()
        
        if tag_obj:
            return tag_obj
        
        tag_obj = TagORM(name=tag_name)
        self.db.add(tag_obj)
        self.db.flush()
        return tag_obj
    
    def create_post(
        self,
        title:str,
        content:str,
        author:Optional[dict],
        tags:List[dict]
    ) -> PostORM:
        author_obj = None
        if author:
            author_obj = self.ensure_author(
                name=author.get("name"),
                email=author.get("email")
            )
        post = PostORM(
            title=title,
            content=content,
            author=author_obj
        )
        for tag in tags:
            tag_obj = self.ensure_tag(tag["name"])
            post.tags.append(tag_obj)
        self.db.add(post)
        self.db.flush()
        self.db.refresh(post)
        return post
    
    def update_post(
        self,
        post:PostORM,
        updates:dict
    ) -> PostORM:
        for key, value in updates.items():
            setattr(post, key, value) 
        self.db.add(post)
        self.db.flush()
        self.db.refresh(post)
        return post
        
    
    def delete_post(self, post:PostORM) -> None:
        self.db.delete(post)
        self.db.flush()