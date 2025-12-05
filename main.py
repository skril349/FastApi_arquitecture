from fastapi import FastAPI, Query, Body, HTTPException
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Union
app = FastAPI(title = "Mini Blog")

BLOG_POST = [
    {"id": 1, "title": "Primer Post", "content": "Este es el contenido del primer post."},
    {"id": 2, "title": "Segundo Post", "content": "Este es el contenido del segundo post."},
    {"id": 3, "title": "Tercer Post", "content": "Este es el contenido del tercer post."}
    ]


class PostBase(BaseModel):
    title: str
    content: str
    
    
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
    
    @field_validator("title")
    @classmethod
    def not_allowed_title(cls,value:str)-> str:
        if "python" in value.lower():
            raise ValueError("El título no puede contener la palabra 'python'")
        return value

class PostUpdate(BaseModel):
    title: str = Field(..., description="Título del post", max_length=100, min_length=1)
    content: Optional[str] = None
    
class PostPublic(PostBase):
    id: int
    
class PostSummary(BaseModel):
    id: int
    title: str


@app.get("/")
def home():
    return {"message": "Bienvenidos a Mini Blog"}

@app.get("/posts", response_model=List[PostPublic])
def list_posts(query: str | None = Query(default=None, description="Buscar en los títulos de los posts")):
    
    if query:
        # list comprehension to filter posts by title
        return [post for post in BLOG_POST if query.lower() in post["title"].lower()]
    return BLOG_POST

@app.get("/posts/{post_id}", response_model=Union[PostPublic, PostSummary], response_description="Post encontrado")
def get_post(post_id:int, include_content: bool = Query(default=True, description="Incluir el contenido del post")):
    
    for post in BLOG_POST:
        if post["id"] == post_id:
            if not include_content:
                return {"id": post["id"], "title": post["title"]}
            return post
    raise HTTPException(status_code=404, detail="Post no encontrado")


@app.post("/posts")
def create_post(post:PostCreate):
    # ... --> obligatori enviar body

    new_id_post = max(post["id"] for post in BLOG_POST) + 1
    post_data = {"id": new_id_post, "title": post.title, "content": post.content}
    BLOG_POST.append(post_data)
    return {"message": "Post creado exitosamente", "data": post_data}

@app.put("/posts/{post_id}")
def update_post(post_id:int, data:PostUpdate):
    for post in BLOG_POST:
        if post["id"] == post_id:
            playload = data.model_dump(exclude_unset=True) # excluye los campos no enviados
            if "title" in playload: post["title"] = playload["title"]
            if "content" in playload: post["content"] = playload["content"]
            return {"message": "Post actualizado exitosamente", "data": post}
    raise HTTPException(status_code=404, detail="Post no encontrado")


@app.delete("/posts/{post_id}")
def delete_post(post_id:int):
    for index, post in enumerate(BLOG_POST):
        if post["id"] == post_id:
            BLOG_POST.pop(index)
            return {"message": "Post eliminado exitosamente"}
    raise HTTPException(status_code=404, detail="Post no encontrado")
