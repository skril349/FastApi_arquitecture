
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.v1.tags.repository import TagRepository
from app.api.v1.tags.schemas import TagCreate, TagPublic, TagUpdate
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
    
@router.put("/{tag_id}",response_model=TagPublic, response_description="actualizar tag", status_code=status.HTTP_202_ACCEPTED)
def update_tag(tag_id:int, data:TagUpdate, db:Session = Depends(get_db), user = Depends(get_current_user)):
    repository = TagRepository(db)
    tag = repository.get(tag_id)
    
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag no encontrado") 
    try:
        updates = data.model_dump(exclude_unset=True) 
        print(f"updates = {updates}" )
        tag = repository.update_tag(tag_id, updates["name"])
        db.commit()
        db.refresh(tag)
        return tag
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al actualizar el tag")


@router.delete("/{tag_id}", status_code=status.HTTP_202_ACCEPTED, response_description="Tag eliminado exitosamente")
def delete_tag(tag_id:int, db: Session = Depends(get_db),user = Depends(get_current_user)): 
    repository = TagRepository(db)
    tag = repository.get(tag_id)
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag no encontrado")
    try:     
        repository.delete_tag(tag_id)
        db.commit()
        return {"message": "Tag eliminado exitosamente"}   
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al eliminar el Tag")
    
@router.get("/popular/top")
def get_most_popular_tag(
    db:Session = Depends(get_db),
    user = Depends(get_current_user)
):
    repository = TagRepository(db)
    row = repository.most_popular()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no hay tags en uso")
    return row