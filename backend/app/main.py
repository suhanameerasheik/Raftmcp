from fastapi import FastAPI

from .config import NODE_ID
from .node import RaftNode


app = FastAPI(title="RaftMCP for Travel")

node = RaftNode(node_id=NODE_ID)


@app.get("/health")
async def health():
    return node.health()