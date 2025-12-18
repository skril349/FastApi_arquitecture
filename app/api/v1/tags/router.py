
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.v1.tags import repository
from app.api.v1.tags.repository import TagRepository
from app.api.v1.tags.schemas import TagCreate, TagPublic
from app.core.db import get_db
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.core.security import get_current_user

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("",response_model=dict)
def list_tags(
    page: int = Query(1, ge=1),
    per_page:int =Query(10,ge = 1, le = 100),
    order_by: str = Query("id", pattern="^(id|name)$"),
    direction: str = Query("asc",pattern="^(asc|desc)$"),
    search: str | None = Query(None),
    db:Session = Depends(get_db)
):
    repository = TagRepository(db)
    return repository.list_tags(page = page,per_page=per_page,order_by=order_by,direction=direction,search=search)

@router.post("",response_model=TagPublic, response_description="post creado", status_code=status.HTTP_201_CREATED)
def create_tag(tag:TagCreate, db:Session = Depends(get_db), user = Depends(get_current_user)):
    repository = TagRepository(db)
    try:
        tag_created = repository.create_tag(tag_name = tag.name)
        db.commit()
        db.refresh(tag_created)
        return tag_created
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="error al crear tag")