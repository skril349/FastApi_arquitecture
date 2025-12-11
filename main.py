import os

from fastapi import FastAPI, Query, Body, HTTPException, Path
from pydantic import BaseModel, Field, field_validator,EmailStr
from typing import Optional, List, Union, Literal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase

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
    
class Author(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, description="Nombre del autor")
    email: Optional[EmailStr] = Field(None, description="Correo electrónico del autor")

class PostBase(BaseModel):
    title: str
    content: str
    tags: Optional[List[Tag]] = Field(default_factory=list) # lista vacía por defecto
    author: Optional[Author] = None
    
    
    
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
    
class PostSummary(BaseModel):
    id: int
    title: str
    
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
        description="Dirección de ordenamiento")
    ):
    
    results = BLOG_POST
    
    query = query or text  # Prioriza 'query' sobre 'text'
    
    if query:
        # list comprehension to filter posts by title
        results =  [post for post in BLOG_POST if query.lower() in post["title"].lower()]
    
    total = len(results)
    
    results = sorted(results, key=lambda post: post[order_by], reverse=(direction=="desc"))
    
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
        items=results[offset: offset + limit]
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
    example=1), include_content: bool = Query(default=True, description="Incluir el contenido del post")):
    
    for post in BLOG_POST:
        if post["id"] == post_id:
            if not include_content:
                return {"id": post["id"], "title": post["title"]}
            return post
    raise HTTPException(status_code=404, detail="Post no encontrado")


@app.post("/posts", response_model=PostPublic, status_code=201)
def create_post(post:PostCreate):
    # ... --> obligatori enviar body

    new_id_post = max(post["id"] for post in BLOG_POST) + 1
    post_data = {"id": new_id_post, "title": post.title, "content": post.content, "tags": [tag.model_dump() for tag in post.tags], "author": post.author.model_dump() if post.author else None}
    BLOG_POST.append(post_data)
    return post_data

@app.put("/posts/{post_id}", response_model=PostPublic)
def update_post(post_id:int, data:PostUpdate):
    for post in BLOG_POST:
        if post["id"] == post_id:
            playload = data.model_dump(exclude_unset=True) # excluye los campos no enviados
            if "title" in playload: post["title"] = playload["title"]
            if "content" in playload: post["content"] = playload["content"]
            return post
    raise HTTPException(status_code=404, detail="Post no encontrado")


@app.delete("/posts/{post_id}")
def delete_post(post_id:int):
    for index, post in enumerate(BLOG_POST):
        if post["id"] == post_id:
            BLOG_POST.pop(index)
            return {"message": "Post eliminado exitosamente"}
    raise HTTPException(status_code=404, detail="Post no encontrado")
