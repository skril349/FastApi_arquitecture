from app.core.db import get_db
from .schemas import PostCreate, PostPublic, PostSummary, PaginatedPost, PostUpdate
from .repository import PostRepository
from typing import List, Optional, Literal, Union
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.core.security import oauth2_scheme, get_current_user
router = APIRouter(prefix ="/posts", tags=["posts"])


@router.get("", response_model=PaginatedPost)
def list_posts(
    text: Optional[str] = Query(
    default=None,
    description="Parametro obsoleto",
    deprecated=True
    ),
    query: Optional[str] = Query(
    default=None,
    description="Buscar en los títulos de los posts",
    alias="q",
    min_length=3,
    max_length=100,
    title="Query de búsqueda",
    example="primer",
    pattern="^[a-zA-Z0-9 ]+$"
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Número máximo de posts a retornar"),
    offset: int = Query(
        default=0,
        ge=0,
        description="Número de posts a omitir"),
    order_by: Literal["title", "id"] = Query(
        "id",
        description="Campo por el cual ordenar los posts",
        example="title"),
    direction: Literal["asc", "desc"] = Query(
        "asc",
        description="Dirección de ordenamiento"),
    db: Session = Depends(get_db)
    ):
    
    offset = offset or 0
    limit = limit or 10
    page=(offset // limit) + 1
    repository = PostRepository(db)
    query = query or text
    total, items = repository.search(
        query=query,
        order_by=order_by,
        direction=direction,
        page=page or 1,
        per_page=limit
    )
    
    return PaginatedPost(
        page=(offset // limit) + 1,
        per_page=limit,
        total_pages=(total + limit -1) // limit,
        has_prev=offset > 0,
        has_next=offset + limit < total,
        order_by=order_by,
        direction=direction,
        search=query,
        total=total,
        limit=limit,
        offset=offset,
        items= items
    )
    

@router.get("/by-tags", response_model=List[PostPublic])
def filter_posts_by_tags(
    tags: List[str] = Query(
        ...,
        min_length=2,
        max_length=30,
        description="Lista de tags para filtrar los posts"),
        db: Session = Depends(get_db)
    ):
    repository = PostRepository(db)
    posts = repository.by_tags(tags)
    return posts
    
    
@router.get("/{post_id}", response_model=Union[PostPublic, PostSummary], response_description="Post encontrado")
def get_post(post_id:int = Path(
    ...,
    description="ID del post a obtener",
    ge=1,
    title="ID del post",
    example=1),
    include_content: bool = Query(default=True, description="Incluir el contenido del post"),
    db: Session = Depends(get_db)):
    
    repository = PostRepository(db)
    post = repository.get(post_id)
        
    if not post:
        raise HTTPException(status_code=404, detail="Post no encontrado")
    
    if include_content:
        return PostPublic.model_validate(post,from_attributes=True)
    else:
        return PostSummary.model_validate(post,from_attributes=True)
    

@router.post("", response_model=PostPublic, status_code=status.HTTP_201_CREATED, response_description="Post creado exitosamente")
def create_post(post:PostCreate, db: Session = Depends(get_db), user = Depends(get_current_user)):
    
    repository = PostRepository(db)
        
    try:
        post = repository.create_post(
            title=post.title,
            content=post.content,
            tags=[tag.model_dump() for tag in post.tags],
            author= post.author.model_dump() if post.author else None
        )
        db.commit()
        db.refresh(post)
        
        return post
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="El título del post ya existe")
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al crear el post")


@router.put("/{post_id}", response_model=PostPublic, status_code=status.HTTP_202_ACCEPTED)
def update_post(post_id:int, data:PostUpdate, db: Session = Depends(get_db),user = Depends(get_current_user)):
    
    repository = PostRepository(db)
    post = repository.get(post_id)
    
    if not post:
        raise HTTPException(status_code=404, detail="Post no encontrado") 
    try:
        updates = data.model_dump(exclude_unset=True) 
        post = repository.update_post(post, updates)
        db.commit()
        db.refresh(post)
        return post
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al actualizar el post")
    

@router.delete("/{post_id}", status_code=status.HTTP_202_ACCEPTED, response_description="Post eliminado exitosamente")
def delete_post(post_id:int, db: Session = Depends(get_db),user = Depends(get_current_user)): 
    repository = PostRepository(db)
    post = repository.get(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post no encontrado")
    try:     
        repository.delete_post(post)
        db.commit()
        return {"message": "Post eliminado exitosamente"}   
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al eliminar el post")
    
@router.get("/secure")
def secure_endpoint(token:str = Depends(oauth2_scheme)):
    return {"message":"acceso con token", "token recibido":token}
    

    
