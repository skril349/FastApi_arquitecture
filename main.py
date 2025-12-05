from fastapi import FastAPI, Query

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
def get_post(post_id:int):
    for post in BLOG_POST:
        if post["id"] == post_id:
            return {"data": post}
    return {"error": "Post no encontrado"}


