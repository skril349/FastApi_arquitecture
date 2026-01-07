from time import perf_counter
from fastapi import FastAPI, Request


def register_middleware(app: FastAPI):
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start = perf_counter()
        response = await call_next(request)
        process_time = perf_counter() - start
        response.headers["X-Process-Time"] = str(process_time)
        return response
    
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        
        method = request.method
        url = request.url
        print(f"ENTRADA: {request.method} {request.url}")
        response = await call_next(request)
        print(f"SALIDA: {method} {url} - {response.status_code}")
        return response
    
