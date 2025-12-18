
from pydantic import BaseModel, ConfigDict, Field, field_validator,EmailStr
from typing import Optional, List, Annotated
from fastapi import Form

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
    image_url: Optional[str] = None
    
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
    #author: Optional[Author] = None
    
    @field_validator("title")
    @classmethod
    def not_allowed_title(cls,value:str)-> str:
        if "python" in value.lower():
            raise ValueError("El título no puede contener la palabra 'python'")
        return value
    
    @classmethod
    def as_form(
        cls,
        title: Annotated[str, Form(min_length = 3)],
        content: Annotated[str, Form(min_length=10)],
        tags: Annotated[Optional[List[str]], Form()] = None
    ):
        tag_objs = [Tag(name=t) for t in tags or []]
        return cls(title=title, content=content, tags = tag_objs)

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

