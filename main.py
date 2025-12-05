from fastapi import FastAPI, Query, Body

app = FastAPI(title = "Mini Blog")

BLOG_POST = [
    {"id": 1, "title": "Primer Post", "content": "Este es el contenido del primer post."},
    {"id": 2, "title": "Segundo Post", "content": "Este es el contenido del segundo post."},
    {"id": 3, "title": "Tercer Post", "content": "Este es el contenido del tercer post."}
    ]

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
    return {"error": "Post no encontrado"}


@app.post("/posts")
# ... --> obligatori enviar body
def create_post(post:dict = Body(...,description="Datos del nuevo post")):
    if "title" not in post or "content" not in post:
        return {"error": "Faltan campos obligatorios: title y content"}
    
    if not str(post["title"]).strip() or not str(post["content"]).strip():
        return {"error": "Los campos title y content no pueden estar vacíos"}
    
    new_id_post = max(post["id"] for post in BLOG_POST) + 1
    post_data = {"id": new_id_post, "title": post["title"], "content": post["content"]}
    BLOG_POST.append(post_data)
    return {"message": "Post creado exitosamente", "data": post_data}

@app.put("/posts/{post_id}")
def update_post(post_id:int, data:dict = Body(...,description="Datos actualizados del post")):
    for post in BLOG_POST:
        if post["id"] == post_id:
            post["title"] = data.get("title", post["title"])
            post["content"] = data.get("content", post["content"])
            return {"message": "Post actualizado exitosamente", "data": post}
    return {"error": "Post no encontrado"}


@app.delete("/posts/{post_id}")
def delete_post(post_id:int):
    for index, post in enumerate(BLOG_POST):
        if post["id"] == post_id:
            BLOG_POST.pop(index)
            return {"message": "Post eliminado exitosamente"}
    return {"error": "Post no encontrado"}
