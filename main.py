from fastapi import FastAPI, Query, Body, HTTPException
from pydantic import BaseModel, Optional
app = FastAPI(title = "Mini Blog")

BLOG_POST = [
    {"id": 1, "title": "Primer Post", "content": "Este es el contenido del primer post."},
    {"id": 2, "title": "Segundo Post", "content": "Este es el contenido del segundo post."},
    {"id": 3, "title": "Tercer Post", "content": "Este es el contenido del tercer post."}
    ]


class PostBase(BaseModel):
    title: str
    content: str
    
class PostCreate(PostBase):
    pass

class PostUpdate(BaseModel):
    title: str
    content: Optional[str] = None


@app.get("/")
def home():
    return {"message": "Bienvenidos a Mini Blog"}

@app.get("/posts")
def list_posts(query: str | None = Query(default=None, description="Buscar en los títulos de los posts")):
    
    if query:
        # list comprehension to filter posts by title
        result = [post for post in BLOG_POST if query.lower() in post["title"].lower()]
        return {"data": result}
    
    return {"data": BLOG_POST}

@app.get("/posts/{post_id}")
def get_post(post_id:int, include_content: bool = Query(default=True, description="Incluir el contenido del post")):
    
    for post in BLOG_POST:
        if post["id"] == post_id:
            if not include_content:
                return {"data": {"id": post["id"], "title": post["title"]}}
            return {"data": post}
    raise HTTPException(status_code=404, detail="Post no encontrado")


@app.post("/posts")
# ... --> obligatori enviar body
def create_post(post:PostCreate):
       
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
