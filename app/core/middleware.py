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
