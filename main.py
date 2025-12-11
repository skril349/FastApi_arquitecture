import os
from datetime import datetime
from fastapi import Depends, FastAPI, Query, Body, HTTPException, Path, status
from pydantic import BaseModel, ConfigDict, Field, field_validator,EmailStr
from typing import Optional, List, Union, Literal
from sqlalchemy import create_engine, Integer, String, Text, DateTime, func,Table,Column, select, UniqueConstraint, ForeignKey
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./blog.db")
print(f"Conectando a la base de datos en: {DATABASE_URL}")

engine_kwargs = {}

if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
    
engine = create_engine(DATABASE_URL,echo = True, future=True, **engine_kwargs)
SessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, class_=Session)

class Base(DeclarativeBase):
    pass

post_tags = Table(
    "post_tags",
    Base.metadata,
    Column("post_id", ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
)

class PostORM(Base):
    __tablename__ = "posts"
    __table_args__ = (UniqueConstraint('title', name='unique_post_title'),)
    
    id : Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title : Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow)
    
    author_id: Mapped[Optional[int]] = mapped_column(ForeignKey("authors.id"), nullable=True)
    author: Mapped[Optional["AuthorORM"]] = relationship(back_populates="posts")
    
    tags: Mapped[List["TagORM"]] = relationship(
        secondary=post_tags,
        back_populates="posts",
        lazy="selectin",
        passive_deletes=True
    )
    
class AuthorORM(Base):
    __tablename__ = "authors"
    id : Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name : Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, unique=True, index=True)
    
    posts: Mapped[List["PostORM"]] = relationship(back_populates="author")
    
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
    
    


Base.metadata.create_all(bind=engine) # dev --> crea las tablas


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        




app = FastAPI(title = "Mini Blog")

BLOG_POST = [
    {"id": 1, "title": "Primer Post", "content": "Este es el contenido del primer post."},
    {"id": 2, "title": "Segundo Post", "content": "Este es el contenido del segundo post."},
    {"id": 3, "title": "Tercer Post", "content": "Este es el contenido del tercer post."},
    {"id": 4, "title": "Cuarto Post", "content": "Este es el contenido del cuarto post."},
    {"id": 5, "title": "Quinto Post", "content": "Este es el contenido del quinto post."},
    {"id": 6, "title": "Sexto Post", "content": "Este es el contenido del sexto post.", "tags": [{"name": "Python"}, {"name": "FastAPI"}]},
    {"id": 7, "title": "Séptimo Post", "content": "Este es el contenido del séptimo post.", "tags": [{"name": "JavaScript"}, {"name": "NodeJS"}]},
    {"id": 8, "title": "Octavo Post", "content": "Este es el contenido del octavo post.", "tags": [{"name": "Python"}, {"name": "Django"}]},
    {"id": 9, "title": "Noveno Post", "content": "Este es el contenido del noveno post."},
    {"id": 10, "title": "Décimo Post", "content": "Este es el contenido del décimo post.", "tags": [{"name": "Go"}, {"name": "Web"}]},
    ]


class Tag(BaseModel):
    name: str = Field(..., min_length=2, max_length=30, description="Nombre de la etiqueta")
    model_config = ConfigDict(from_attributes=True)
    
class Author(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, description="Nombre del autor")
    email: Optional[EmailStr] = Field(None, description="Correo electrónico del autor")
    model_config = ConfigDict(from_attributes=True)

class PostBase(BaseModel):
    title: str
    content: str
    tags: Optional[List[Tag]] = Field(default_factory=list) # lista vacía por defecto
    author: Optional[Author] = None
    model_config = ConfigDict(from_attributes=True)
    
class PostCreate(BaseModel):
    title: str = Field(
        ...,
        description="Título del post",
        max_length=100, min_length=1,
        examples=["Mi primer post"]
        )
    content: Optional[str] = Field(
        default="Contenido no disponible",
        description="Contenido del post",
        examples=["Este es el contenido de mi primer post."], 
        max_length=1000,
        min_length=10
        )
    
    tags: List[Tag] = Field(default_factory=list)
    author: Optional[Author] = None
    
    @field_validator("title")
    @classmethod
    def not_allowed_title(cls,value:str)-> str:
        if "python" in value.lower():
            raise ValueError("El título no puede contener la palabra 'python'")
        return value

class PostUpdate(BaseModel):
    title: Optional[str] = Field(None, description="Título del post", max_length=100, min_length=1)
    content: Optional[str] = None
    
class PostPublic(PostBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
    
class PostSummary(BaseModel):
    id: int
    title: str
    model_config = ConfigDict(from_attributes=True)
    
class PaginatedPost(BaseModel):
    page:int
    per_page:int
    total: int
    total_pages: int
    has_prev: bool
    has_next: bool
    order_by: str
    direction: str
    search: Optional[str]
    limit: int
    offset: int
    items: List[PostPublic]


@app.get("/")
def home():
    return {"message": "Bienvenidos a Mini Blog"}

@app.get("/posts", response_model=PaginatedPost)
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
    
    results = select(PostORM)
    
    query = query or text  # Prioriza 'query' sobre 'text'
    
    if query:
        # list comprehension to filter posts by title
        results =  results.where(PostORM.title.ilike(f"%{query}%"))
    
    total = db.scalar(select(func.count()).select_from(results.subquery()))
    
    if order_by == "id":
        order_column = PostORM.id
    else:
        order_column = func.lower(PostORM.title)
    
    results = results.order_by(order_column.asc() if direction == "asc" else order_column.desc())

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
        items=db.execute(results.offset(offset).limit(limit)).scalars().all()
    )
    

@app.get("/posts/by-tags", response_model=List[PostPublic])
def filter_posts_by_tags(
    tags: List[str] = Query(
        ...,
        min_length=2,
        max_length=30,
        description="Lista de tags para filtrar los posts")):
    
    tags_lower = [tag.lower() for tag in tags]
    
    results = [post for post in BLOG_POST if any(tag["name"].lower() in tags_lower for tag in post.get("tags", []))]
    return results


@app.get("/posts/{post_id}", response_model=Union[PostPublic, PostSummary], response_description="Post encontrado")
def get_post(post_id:int = Path(
    ...,
    description="ID del post a obtener",
    ge=1,
    title="ID del post",
    example=1),
    include_content: bool = Query(default=True, description="Incluir el contenido del post"),
    db: Session = Depends(get_db)):
    
    post_find = select(PostORM).where(PostORM.id == post_id)
    post = db.execute(post_find).scalar_one_or_none()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post no encontrado")
    
    if include_content:
        return PostPublic.model_validate(post,from_attributes=True)
    else:
        return PostSummary.model_validate(post,from_attributes=True)
    


@app.post("/posts", response_model=PostPublic, status_code=status.HTTP_201_CREATED, response_description="Post creado exitosamente")
def create_post(post:PostCreate, db: Session = Depends(get_db)):
    # ... --> obligatori enviar body
    
    author_obj = None
    if post.author:
       author_obj = db.execute(
            select(AuthorORM).where(AuthorORM.email == post.author.email)
        ).scalar_one_or_none()
       
    if not author_obj:
        author_obj = AuthorORM(
            name=post.author.name,
            email=post.author.email
        )
        db.add(author_obj)
        db.flush()   
     
    new_post = PostORM(
        title=post.title,
        content=post.content,
        author = author_obj
    )
    
    for tag in post.tags:
        tag_obj = db.execute(
            select(TagORM).where(TagORM.name.ilike(tag.name))
        ).scalar_one_or_none()
        if not tag_obj:
            tag_obj = TagORM(name=tag.name)
            db.add(tag_obj)
            db.flush()
        new_post.tags.append(tag_obj)
        
    try:
        db.add(new_post)
        db.commit()
        db.refresh(new_post)
        return new_post
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="El título del post ya existe")
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al crear el post")


@app.put("/posts/{post_id}", response_model=PostPublic, status_code=status.HTTP_202_ACCEPTED)
def update_post(post_id:int, data:PostUpdate, db: Session = Depends(get_db)):
    
    post_find = select(PostORM).where(PostORM.id == post_id)
    post = db.execute(post_find).scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post no encontrado")
    
    
    updates = data.model_dump(exclude_unset=True) # excluye los campos no enviados
    for key, value in updates.items():
        setattr(post, key, value)
        
    try:
        db.add(post)
        db.commit()
        db.refresh(post)
        return post
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al actualizar el post")
    


@app.delete("/posts/{post_id}", status_code=status.HTTP_202_ACCEPTED, response_description="Post eliminado exitosamente")
def delete_post(post_id:int, db: Session = Depends(get_db)):
    
    post_find = select(PostORM).where(PostORM.id == post_id)
    post = db.execute(post_find).scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post no encontrado")
    try:
        db.delete(post)
        db.commit()
        return {"message": "Post eliminado exitosamente"}   
     
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al eliminar el post")
    
