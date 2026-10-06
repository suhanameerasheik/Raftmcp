from app.raft.node import RaftRuntime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.mcp.tools import invoke_tool, list_tools
from app.travel.simulator import get_bookings
from app.config import NODE_ID


app = FastAPI(title="RaftMCP Travel")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# Raft node
# --------------------------------------------------

raft_node = RaftRuntime(
    node_id=NODE_ID,
)


# --------------------------------------------------
# Helper
# --------------------------------------------------

def call_tool(name: str, arguments: dict):
    try:
        return invoke_tool(name, arguments)
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


# --------------------------------------------------
# Health
# --------------------------------------------------

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "node_id": NODE_ID,
        "is_active": True,
    }


# --------------------------------------------------
# Raft status
# --------------------------------------------------

@app.get("/raft/status")
async def raft_status():
    return {
        "node_id": NODE_ID,
        "state": raft_node.state,
        "term": raft_node.current_term,
        "leader_id": raft_node.leader_id,
    }


# --------------------------------------------------
# Tool registry
# --------------------------------------------------

@app.get("/tools")
async def tools():
    return {
        "tools": list_tools()
    }


@app.get("/registry/tools")
async def registry_tools():
    return {
        "tools": list_tools()
    }


# --------------------------------------------------
# Travel demo request
# --------------------------------------------------

@app.post("/demo/travel-request")
async def travel_request(payload: dict):
    request = payload.get("request", "")

    if not request:
        raise HTTPException(
            status_code=400,
            detail="Request is required",
        )

    return {
        "request": request,
        "status": "processed",
        "message": "Travel request received successfully.",
        "node_id": NODE_ID,
    }


# --------------------------------------------------
# Flight tools
# --------------------------------------------------

@app.post("/tools/search_flights")
async def search_flights(arguments: dict):
    return call_tool(
        "search_flights",
        arguments,
    )


@app.post("/tools/check_flight_status")
async def check_flight_status(arguments: dict):
    return call_tool(
        "check_flight_status",
        arguments,
    )


# --------------------------------------------------
# Hotel tools
# --------------------------------------------------

@app.post("/tools/search_hotels")
async def search_hotels(arguments: dict):
    return call_tool(
        "search_hotels",
        arguments,
    )


@app.post("/tools/book_hotel")
async def book_hotel(arguments: dict):
    return call_tool(
        "book_hotel",
        arguments,
    )
@app.get("/trips")
async def trips():
    return {
        "trips": get_bookings()
    }

# --------------------------------------------------
# AI Travel Agent
# --------------------------------------------------

@app.post("/agent/request")
async def agent_request(payload: dict):
    request = payload.get("request", "")

    if not request:
        raise HTTPException(
            status_code=400,
            detail="Request is required",
        )

    request_lower = request.lower()

    # Flight search
    if "flight" in request_lower and (
        "search" in request_lower
        or "find" in request_lower
        or "flight from" in request_lower
    ):
        return {
            "agent": "travel-agent",
            "intent": "search_flights",
            "message": "Flight search request received.",
            "next_step": "Use the search_flights MCP tool.",
        }

    # Flight status
    if "flight status" in request_lower:
        return {
            "agent": "travel-agent",
            "intent": "check_flight_status",
            "message": "Flight status request received.",
            "next_step": "Use the check_flight_status MCP tool.",
        }

    # Hotel search
    if "hotel" in request_lower and (
        "search" in request_lower
        or "find" in request_lower
        or "hotel in" in request_lower
    ):
        return {
            "agent": "travel-agent",
            "intent": "search_hotels",
            "message": "Hotel search request received.",
            "next_step": "Use the search_hotels MCP tool.",
        }

    # Hotel booking
    if "book" in request_lower and "hotel" in request_lower:
        return {
            "agent": "travel-agent",
            "intent": "book_hotel",
            "message": "Hotel booking request received.",
            "next_step": "Use the book_hotel MCP tool.",
        }

    return {
        "agent": "travel-agent",
        "intent": "unknown",
        "message": "I could not determine the travel request.",
    }
