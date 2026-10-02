import asyncio
import os
import tempfile
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException

from .config import NODE_ID, PEERS
from .node import RaftNode

from .raft.node import RaftRuntime
from .raft.messages import (
    RequestVoteRequest,
    HeartbeatRequest,
    AppendEntriesRequest,
)
from .raft.heartbeat import HeartbeatManager

from .har.parser import parse_har
from .har.extractor import extract_travel_requests
from .har.sanitizer import sanitize_request
from .har.generator import generate_tool_definitions

from .mcp.server import call_tool, get_registered_tools


node = RaftNode(node_id=NODE_ID)

raft = RaftRuntime(
    node_id=NODE_ID,
    peers=PEERS,
)

heartbeat_manager = HeartbeatManager(
    raft.state,
    raft.election,
    peers=PEERS,
)

generated_tools = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    election_task = asyncio.create_task(
        raft.run_election_loop()
    )
    heartbeat_task = asyncio.create_task(
        heartbeat_manager.run_heartbeat_loop()
    )

    try:
        yield
    finally:
        election_task.cancel()
        heartbeat_task.cancel()

        await asyncio.gather(
            election_task,
            heartbeat_task,
            return_exceptions=True,
        )


app = FastAPI(
    title="RaftMCP for Travel",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    return node.health()


@app.get("/raft/status")
async def raft_status():
    return raft.status()


@app.get("/raft/log")
async def raft_log():
    return raft.log_status()


@app.post("/raft/request-vote")
async def request_vote(request: RequestVoteRequest):
    return raft.handle_request_vote(request)


@app.post("/raft/heartbeat")
async def receive_heartbeat(request: HeartbeatRequest):
    return heartbeat_manager.receive_heartbeat(request)


@app.post("/raft/append-entries")
async def append_entries(request: AppendEntriesRequest):
    return raft.handle_append_entries(request)


@app.post("/raft/command")
async def submit_command(command: dict):
    if raft.state.role != raft.state.role.LEADER:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "This node is not the leader.",
                "leader_id": raft.state.leader_id,
            },
        )

    if command.get("command") != "ADD_TOOL":
        raise HTTPException(
            status_code=400,
            detail="Unsupported command. Use ADD_TOOL.",
        )

    tool = command.get("tool")
    if not isinstance(tool, dict) or not tool.get("name"):
        raise HTTPException(
            status_code=400,
            detail="ADD_TOOL requires a tool object with a name.",
        )

    return await raft.submit_command(command)


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