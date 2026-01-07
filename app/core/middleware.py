from time import perf_counter
import uuid
from fastapi import FastAPI, HTTPException, Request


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
    
    @app.middleware("http")
    async def add_request_id_header(request: Request, call_next):
        request_id = str(uuid.uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    
    @app.middleware("http")
    async def block_ip_middleware(request: Request, call_next):
        blocked_ips = {"192.168.1.100"}
        client_ip = request.client.host
        if client_ip in blocked_ips:
            raise HTTPException(status_code=403, detail="Access forbidden from your IP address.")
        return await call_next(request)
