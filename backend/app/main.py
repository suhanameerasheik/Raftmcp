import os
import tempfile

from fastapi import FastAPI, File, UploadFile, HTTPException

from .config import NODE_ID
from .node import RaftNode

from .har.parser import parse_har
from .har.extractor import extract_travel_requests
from .har.sanitizer import sanitize_request
from .har.generator import generate_tool_definitions

from .mcp.server import call_tool, get_registered_tools


app = FastAPI(title="RaftMCP for Travel")

node = RaftNode(node_id=NODE_ID)

generated_tools = []


@app.get("/health")
async def health():
    return node.health()


@app.post("/tools/generate")
async def generate_tools(file: UploadFile = File(...)):
    contents = await file.read()

    with tempfile.NamedTemporaryFile(
        suffix=".har",
        delete=False,
    ) as temp_file:
        temp_file.write(contents)
        temp_path = temp_file.name

    try:
        har_data = parse_har(temp_path)

        extracted_requests = extract_travel_requests(har_data)

        sanitized_requests = [
            sanitize_request(request)
            for request in extracted_requests
        ]

        tools = generate_tool_definitions(sanitized_requests)

        generated_tools.clear()
        generated_tools.extend(tools)

        return {
            "count": len(tools),
            "tools": tools,
        }

    finally:
        os.unlink(temp_path)


@app.get("/tools")
async def get_tools():
    return {
        "count": len(generated_tools),
        "tools": generated_tools,
    }


@app.get("/mcp/tools")
async def list_mcp_tools():
    return {
        "count": len(get_registered_tools()),
        "tools": get_registered_tools(),
    }


@app.post("/tools/search_flights")
async def search_flights(arguments: dict):
    try:
        return call_tool("search_flights", arguments)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.post("/tools/check_flight_status")
async def check_flight_status(arguments: dict):
    try:
        return call_tool("check_flight_status", arguments)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.post("/tools/search_hotels")
async def search_hotels(arguments: dict):
    try:
        return call_tool("search_hotels", arguments)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
