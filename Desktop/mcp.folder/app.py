
import os
import secrets
from contextlib import asynccontextmanager, AsyncExitStack

from mcp.server.transport_security import TransportSecuritySettings
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from mcp_server import mcp

load_dotenv(override=True)

API_KEY = os.getenv("MCP_API_KEY")




@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncExitStack() as stack:
        await stack.enter_async_context(
            mcp.session_manager.run()
        )
        yield


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.middleware("http")
async def verify_api_key(request: Request, call_next):

    if request.url.path == "/health":
        return await call_next(request)

    supplied_key = request.headers.get("X-API-Key")

    if not API_KEY or not supplied_key or not secrets.compare_digest(
    supplied_key, API_KEY
):
        return JSONResponse(
            status_code=401,
            content={"error": "Unauthorized. Invalid or missing API key."}
        )

    return await call_next(request)

app.mount(
    "/",
    mcp.streamable_http_app(
        transport_security=TransportSecuritySettings(
            allowed_hosts=[
                "datainsight-mcp.redocean-2ac59ce2.southafricanorth.azurecontainerapps.io",
                "datainsight-mcp.redocean-2ac59ce2.southafricanorth.azurecontainerapps.io:*"
            ]
        )
    )
)



