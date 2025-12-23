
import typer

from app.seeds.service import run_all, run_categories, run_tags, run_users 


app = typer.Typer(help="Seeds: users, categories, tags")


@app.command("all")
def all_():
    run_all()
    typer.echo("Todos los seeds cargados")
    
@app.command("users")
def users():
    run_users()
    typer.echo("usuarios cargados")
    
@app.command("categories")
def categories():
    run_categories()
    typer.echo("categorias cargadas")
    
@app.command("tags")
def tags():
    run_tags()
    typer.echo("Tags cargados")
    
    
